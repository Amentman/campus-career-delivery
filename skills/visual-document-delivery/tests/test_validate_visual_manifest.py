import copy
import sys
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

from validate_visual_manifest import validate_manifest


def complete_manifest():
    return {
        "skill": "student-role-interview-prep",
        "visual_contract": {
            "substantial": True,
            "complexity_signals": ["multi_step_flow", "role_handoff"],
            "required_visual_ids": ["business-flow"],
            "visual_plan": [
                {
                    "id": "business-flow",
                    "type": "flowchart",
                    "reason": "The reader must understand a branched shipper-driver workflow.",
                    "section": "Business flow",
                    "fact_boundary": "Inferred",
                    "caption": "Public-business abstraction; not an internal product screen.",
                    "source_note": "Official public business pages and the supplied JD.",
                }
            ],
            "readback": {
                "media_blocks": [
                    {
                        "visual_id": "business-flow",
                        "block_type": "image",
                        "token": "non-empty-token",
                        "section": "Business flow",
                    }
                ]
            },
            "render_qa": {
                "page_count": 3,
                "checked_pages": [1, 2, 3],
                "checked_items": ["clipping", "readability", "layout", "caption"],
                "issues": [],
            },
            "quality_review": [
                {
                    "visual_id": "business-flow",
                    "reader_question": "Who hands a shipment to whom?",
                    "target_width_px": 760,
                    "evidence": ["render/business-flow-at-760.png"],
                    "checks": {
                        "meaning": "The three service roles attach to their actual handoff stages.",
                        "logic": "The failed handoff ends with the dispatcher; success ends with delivery.",
                        "hierarchy": "The main route is read before the two exception branches.",
                        "legibility": "All branch labels are readable at the declared width without zooming.",
                        "visual_utility": "The branching route makes the two different owners visible together.",
                    },
                    "verdict": "pass",
                    "issues": [],
                }
            ],
        },
    }


class VisualManifestTests(unittest.TestCase):
    def test_uploaded_and_rendered_is_not_a_quality_review(self):
        data = complete_manifest()
        data["visual_contract"].pop("quality_review")
        self.assertTrue(any("quality review missing" in x for x in validate_manifest(data)))

    def test_unverified_or_failed_figure_prevents_completion(self):
        for verdict in ("unverified", "revise"):
            with self.subTest(verdict=verdict):
                data = complete_manifest()
                data["visual_contract"]["quality_review"][0]["verdict"] = verdict
                self.assertTrue(any("quality review not passed" in x for x in validate_manifest(data)))

    def test_quality_review_needs_target_width_and_actual_evidence(self):
        data = complete_manifest()
        review = data["visual_contract"]["quality_review"][0]
        review["target_width_px"] = 0
        review["evidence"] = []
        errors = validate_manifest(data)
        self.assertTrue(any("target_width_px" in x for x in errors))
        self.assertTrue(any("quality evidence" in x for x in errors))

    def test_pass_cannot_hide_a_known_visual_issue(self):
        data = complete_manifest()
        data["visual_contract"]["quality_review"][0]["issues"] = ["Title promises three layers, figure shows five unrelated rows."]
        self.assertTrue(any("quality review has unresolved issues" in x for x in validate_manifest(data)))

    def test_local_review_covers_all_affected_sections_without_claiming_full_document(self):
        data = complete_manifest()
        data["visual_contract"]["render_qa"].update({
            "scope": "affected_sections", "required_sections": ["Business flow"],
            "checked_sections": ["Business flow"], "page_count": 12, "checked_pages": [3, 4],
        })
        self.assertEqual(validate_manifest(data), [])
        data["visual_contract"]["render_qa"]["checked_sections"] = []
        self.assertTrue(any("affected sections" in x for x in validate_manifest(data)))

    def test_complete_substantial_document_passes(self):
        self.assertEqual(validate_manifest(complete_manifest()), [])

    def test_complex_document_without_visual_fails(self):
        data = complete_manifest()
        data["visual_contract"]["visual_plan"] = []
        self.assertIn(
            "substantial document with complex relationships needs a visual plan",
            validate_manifest(data),
        )

    def test_empty_media_token_fails(self):
        data = complete_manifest()
        data["visual_contract"]["readback"]["media_blocks"][0]["token"] = ""
        self.assertIn(
            "media token is empty: business-flow", validate_manifest(data)
        )

    def test_readback_src_is_a_valid_media_identifier(self):
        data = complete_manifest()
        media = data["visual_contract"]["readback"]["media_blocks"][0]
        media.pop("token")
        media["src"] = "synthetic-rendered-image"
        self.assertEqual(validate_manifest(data), [])

    def test_whitespace_media_src_is_not_accepted(self):
        data = complete_manifest()
        media = data["visual_contract"]["readback"]["media_blocks"][0]
        media.pop("token")
        media["src"] = "  "
        self.assertIn("media token is empty: business-flow", validate_manifest(data))

    def test_incomplete_page_review_fails(self):
        data = complete_manifest()
        data["visual_contract"]["render_qa"]["checked_pages"] = [1, 3]
        self.assertIn(
            "render QA does not cover every page", validate_manifest(data)
        )

    def test_chart_requires_source_metric_time_and_units(self):
        data = complete_manifest()
        chart = data["visual_contract"]["visual_plan"][0]
        chart["type"] = "chart"
        chart["chart_metadata"] = {
            "source_identity": "Official labor-market dataset",
            "metric_definition": "Share of postings mentioning SQL",
            "time_range": "2025-01-01 to 2025-12-31",
            "unit_or_denominator": "",
        }
        errors = validate_manifest(data)
        self.assertIn(
            "chart metadata field is empty: business-flow.unit_or_denominator",
            errors,
        )

    def test_simple_document_may_explain_why_no_visual_is_needed(self):
        data = {
            "skill": "building-resume-interview-stories",
            "visual_contract": {
                "substantial": False,
                "complexity_signals": [],
                "required_visual_ids": [],
                "visual_plan": [],
                "no_visual_reason": (
                    "Single resume bullet rewrite with no multi-part relationship."
                ),
                "readback": {"media_blocks": []},
                "render_qa": {
                    "page_count": 0,
                    "checked_pages": [],
                    "checked_items": [],
                    "issues": [],
                },
            },
        }
        self.assertEqual(validate_manifest(data), [])


if __name__ == "__main__":
    unittest.main()
