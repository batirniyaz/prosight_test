from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.roles import LIMITED_REGION_IDS
from .models import Locus, LocusMember

LOCUS_URL = "/locus"

LOCUS_FIELDS = {
    "id", "assemblyId", "locusName", "publicLocusName", "chromosome",
    "strand", "locusStart", "locusStop", "memberCount",
}
MEMBER_FIELDS = {"locusMemberId", "ursTaxid", "regionId", "membershipStatus"}

ALLOWED_REGION, OTHER_ALLOWED_REGION = LIMITED_REGION_IDS[0], LIMITED_REGION_IDS[1]
FORBIDDEN_REGION, ANOTHER_FORBIDDEN_REGION = 555, 999


class LocusApiTestBase(APITestCase):
    databases = {"default", "rnacentral"}

    @classmethod
    def setUpTestData(cls):
        # Locus 1: one allowed and one forbidden region -> limited sees it, but only one member
        # Locus 2: forbidden region only                 -> limited doesn't see it
        # Locus 3: allowed region, other assembly
        loci = [
            Locus(id=1, assembly_id="GRCh38", locus_name="l1", public_locus_name="PUB1",
                  chromosome="1", strand="+", locus_start=300, locus_stop=400, member_count=2),
            Locus(id=2, assembly_id="GRCh38", locus_name="l2", public_locus_name="PUB2",
                  chromosome="2", strand="-", locus_start=100, locus_stop=200, member_count=1),
            Locus(id=3, assembly_id="GRCm39", locus_name="l3", public_locus_name="PUB3",
                  chromosome="X", strand="+", locus_start=200, locus_stop=250, member_count=1),
        ]
        Locus.objects.bulk_create(loci)
        LocusMember.objects.bulk_create([
            LocusMember(id=11, locus_id=1, urs_taxid="URS0000000011_9606",
                        region_id=ALLOWED_REGION, membership_status="member"),
            LocusMember(id=12, locus_id=1, urs_taxid="URS0000000012_9606",
                        region_id=ANOTHER_FORBIDDEN_REGION, membership_status="highlighted"),
            LocusMember(id=21, locus_id=2, urs_taxid="URS0000000021_9606",
                        region_id=FORBIDDEN_REGION, membership_status="member"),
            LocusMember(id=31, locus_id=3, urs_taxid="URS0000000031_10090",
                        region_id=OTHER_ALLOWED_REGION, membership_status="member"),
        ])

    def login(self, username):
        user = User.objects.get(username=username)
        token = RefreshToken.for_user(user).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def get_locus(self, **params):
        return self.client.get(LOCUS_URL, params)

    def ids(self, response):
        return [item["id"] for item in response.json()["data"]]


class AuthTests(LocusApiTestBase):
    def test_token_is_issued_for_predefined_user(self):
        response = self.client.post("/auth/token", {"username": "admin", "password": "admin"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.json())

    def test_wrong_password_is_rejected(self):
        response = self.client.post("/auth/token", {"username": "admin", "password": "wrong"})
        self.assertEqual(response.status_code, 401)

    def test_anonymous_request_is_rejected(self):
        self.assertEqual(self.get_locus().status_code, 401)

    def test_invalid_token_is_rejected(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer not-a-token")
        self.assertEqual(self.get_locus().status_code, 401)


class ResponseFormatTests(LocusApiTestBase):
    def setUp(self):
        self.login("admin")

    def test_flat_list_without_sideloading(self):
        response = self.get_locus()
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["meta"], {"page": 1, "limit": 1000, "total": 3})
        for item in body["data"]:
            self.assertEqual(set(item), LOCUS_FIELDS)

    def test_sideloading_adds_nested_members(self):
        response = self.get_locus(sideloading="locusMembers")
        self.assertEqual(response.status_code, 200)
        first = response.json()["data"][0]
        self.assertEqual(set(first), LOCUS_FIELDS | {"locusMembers"})
        self.assertEqual(len(first["locusMembers"]), 2)
        self.assertEqual(set(first["locusMembers"][0]), MEMBER_FIELDS)

    def test_sideloading_does_not_cause_n_plus_one(self):
        # count + loci + one prefetch query for all members
        with self.assertNumQueries(3, using="rnacentral"):
            self.get_locus(sideloading="locusMembers")


class PermissionTests(LocusApiTestBase):
    def test_admin_sees_everything(self):
        self.login("admin")
        self.assertEqual(self.ids(self.get_locus()), [1, 2, 3])

    def test_normal_gets_rl_data_only(self):
        self.login("normal")
        response = self.get_locus()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.ids(response), [1, 2, 3])
        self.assertNotIn("locusMembers", response.json()["data"][0])

    def test_normal_cannot_sideload(self):
        self.login("normal")
        self.assertEqual(self.get_locus(sideloading="locusMembers").status_code, 403)

    def test_limited_sees_only_allowed_regions(self):
        self.login("limited")
        response = self.get_locus()
        self.assertEqual(self.ids(response), [1, 3])
        self.assertEqual(response.json()["meta"]["total"], 2)

    def test_limited_sideloading_hides_forbidden_members(self):
        self.login("limited")
        data = self.get_locus(sideloading="locusMembers").json()["data"]
        regions = {m["regionId"] for locus in data for m in locus["locusMembers"]}
        self.assertEqual(regions, {ALLOWED_REGION, OTHER_ALLOWED_REGION})

    def test_limited_cannot_reach_forbidden_locus_by_id(self):
        self.login("limited")
        self.assertEqual(self.ids(self.get_locus(id="2")), [])


class FilterTests(LocusApiTestBase):
    def setUp(self):
        self.login("admin")

    def test_filter_by_multiple_ids(self):
        self.assertEqual(self.ids(self.get_locus(id="1,3")), [1, 3])

    def test_filter_by_assembly_id(self):
        self.assertEqual(self.ids(self.get_locus(assemblyId="GRCm39")), [3])

    def test_filter_by_multiple_region_ids(self):
        self.assertEqual(self.ids(self.get_locus(regionId=f"{FORBIDDEN_REGION},{OTHER_ALLOWED_REGION}")), [2, 3])

    def test_filter_by_membership_status(self):
        self.assertEqual(self.ids(self.get_locus(membershipStatus="highlighted")), [1])

    def test_member_filter_does_not_duplicate_loci(self):
        # both members of locus 1 match -> the locus must appear once
        response = self.get_locus(regionId=f"{ALLOWED_REGION},{ANOTHER_FORBIDDEN_REGION}")
        self.assertEqual(self.ids(response), [1])
        self.assertEqual(response.json()["meta"]["total"], 1)


class SortingTests(LocusApiTestBase):
    def setUp(self):
        self.login("admin")

    def test_sort_ascending(self):
        self.assertEqual(self.ids(self.get_locus(sort="locusStart")), [2, 3, 1])

    def test_sort_descending(self):
        self.assertEqual(self.ids(self.get_locus(sort="-locusStart")), [1, 3, 2])

    def test_sort_by_multiple_fields(self):
        self.assertEqual(self.ids(self.get_locus(sort="assemblyId,-locusStart")), [1, 2, 3])


class PaginationTests(LocusApiTestBase):
    def setUp(self):
        self.login("admin")

    def test_custom_limit_and_page(self):
        response = self.get_locus(limit=2, page=2)
        self.assertEqual(self.ids(response), [3])
        self.assertEqual(response.json()["meta"], {"page": 2, "limit": 2, "total": 3})

    def test_limit_is_capped(self):
        self.assertEqual(self.get_locus(limit=5000).json()["meta"]["limit"], 1000)


class SchemaTests(LocusApiTestBase):
    def test_openapi_schema_is_available(self):
        self.assertEqual(self.client.get("/schema/").status_code, 200)
