import json
import hashlib
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"


class RepositoryContractTests(unittest.TestCase):
    def test_plugin_contains_complete_student_delivery_skill_suite(self):
        expected = {
            "auditing-candidate-resumes",
            "building-resume-interview-stories",
            "campus-job-matching",
            "campus-recommend",
            "delivering-student-career-plans",
            "designing-student-portfolio-products",
            "recording-processing",
            "revising-and-delivering-resumes",
            "student-mock-interview-delivery",
            "student-role-interview-prep",
            "student-interview-review-delivery",
            "student-job-content",
            "visual-document-delivery",
            "job-sales-advisor",
            "job-content-publisher",
            "xiaohongshu-image-renderer",
            "multi-source-todo-control",
            "personal-todo-control",
    "jihui-interview",
    "pengyouquan-copywriting",
    "tencent-meeting-cloud-export",
    "writing-readable-documents",
        }
        actual = {path.name for path in SKILLS.iterdir() if (path / "SKILL.md").is_file()}
        self.assertEqual(expected, actual)

    def test_skill_names_match_their_directories(self):
        for skill_dir in SKILLS.iterdir():
            skill_file = skill_dir / "SKILL.md"
            if not skill_file.is_file():
                continue
            text = skill_file.read_text(encoding="utf-8")
            match = re.search(r"^name:\s*([^\n]+)$", text, re.MULTILINE)
            self.assertIsNotNone(match, skill_file)
            self.assertEqual(skill_dir.name, match.group(1).strip())

    def test_markdown_references_are_local_and_resolvable(self):
        link_pattern = re.compile(r"\[[^\]]+\]\(([^)]+\.md)\)")
        for markdown in SKILLS.rglob("*.md"):
            if 'node_modules' in markdown.parts:
                continue
            text = markdown.read_text(encoding="utf-8")
            for target in link_pattern.findall(text):
                if "://" in target:
                    continue
                self.assertFalse(target.startswith("/"), f"absolute link in {markdown}: {target}")
                self.assertTrue((markdown.parent / target).resolve().is_file(), f"missing link in {markdown}: {target}")

    def test_interview_review_requests_route_to_the_dedicated_review_skill(self):
        mock_text = (SKILLS / "student-mock-interview-delivery" / "SKILL.md").read_text(encoding="utf-8")
        role_text = (SKILLS / "student-role-interview-prep" / "SKILL.md").read_text(encoding="utf-8")
        recording = (SKILLS / "recording-processing" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("student-interview-review-delivery", mock_text)
        self.assertIn("student-mock-interview-delivery", role_text)
        self.assertIn("student-interview-review-delivery", recording)

    def test_project_contract_defines_feishu_student_delivery_lifecycle(self):
        project_rules = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        contract = project_rules + "\n" + readme
        required_terms = (
            "学生唯一飞书主页",
            "姓名｜面试指导者版（内部）",
            "姓名｜学生面试准备版",
            "专岗准备｜公司｜岗位",
            "面试复盘｜公司｜日期",
            "正式、可归档的学生材料默认写入唯一飞书页面",
            "正文图片",
            "学生端",
        )
        for term in required_terms:
            self.assertIn(term, contract, term)

    def test_interview_routes_use_the_shared_page_tree_and_feishu_default(self):
        mock_text = (SKILLS / "student-mock-interview-delivery" / "SKILL.md").read_text(encoding="utf-8")
        role_text = (SKILLS / "student-role-interview-prep" / "SKILL.md").read_text(encoding="utf-8")
        review_text = (SKILLS / "student-interview-review-delivery" / "SKILL.md").read_text(encoding="utf-8")

        for text in (mock_text, role_text, review_text):
            self.assertIn("学生唯一飞书主页", text)
            self.assertIn("姓名｜面试指导者版（内部）", text)
            self.assertIn("姓名｜学生面试准备版", text)
            self.assertIn("正式、可归档的学生材料默认写入唯一飞书页面", text)
        self.assertIn("专岗准备｜公司｜岗位", role_text)
        self.assertIn("面试复盘｜公司｜日期", review_text)
        self.assertIn("独立子页", role_text)
        self.assertIn("独立子页", review_text)

    def test_feishu_interview_visuals_default_to_native_boards_and_preserve_media(self):
        reference_paths = (
            SKILLS / "student-mock-interview-delivery" / "references" / "feishu-delivery-contract.md",
            SKILLS / "student-interview-review-delivery" / "references" / "feishu-boundary-and-acceptance.md",
        )
        for path in reference_paths:
            text = path.read_text(encoding="utf-8")
            self.assertIn("正文", text, path)
            self.assertIn("原生画板", text, path)
            self.assertIn("impeccable", text, path)
            self.assertIn("原生节点", text, path)
            self.assertNotIn("必须使用**飞书原生画板**", text, path)
            self.assertNotIn("必须使用飞书原生画板", text, path)
            self.assertIn("no_visual_reason", text, path)
        role_text = (SKILLS / "student-role-interview-prep" / "references" / "feishu-boundary-and-acceptance.md").read_text(encoding="utf-8")
        self.assertIn("原生画板", role_text)
        self.assertIn("逐图", role_text)
        self.assertIn("不能代替正文可见画板", role_text)
        quality_text = (SKILLS / "student-mock-interview-delivery" / "references" / "interview-quality-contract.md").read_text(encoding="utf-8")
        self.assertNotIn("真实流程图或飞书画板", quality_text)

    def test_supporting_workflows_route_student_durable_outputs_to_feishu(self):
        story_text = (SKILLS / "building-resume-interview-stories" / "SKILL.md").read_text(encoding="utf-8")
        recording_text = (SKILLS / "recording-processing" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("正式、可归档的学生材料默认写入唯一飞书页面", story_text)
        self.assertIn("学生唯一飞书主页", story_text)
        self.assertIn("Markdown", story_text)
        self.assertIn("student-interview-review-delivery", recording_text)
        self.assertIn("学生交付", recording_text)
        self.assertIn("飞书", recording_text)
        self.assertIn("no_visual_reason", recording_text)
        for text in (story_text, recording_text):
            self.assertIn("姓名｜面试指导者版（内部）", text)
            self.assertIn("姓名｜学生面试准备版", text)
            self.assertIn("专岗准备｜公司｜岗位", text)
            self.assertIn("面试复盘｜公司｜日期", text)

    def test_visual_contract_is_target_format_aware(self):
        visual_text = (SKILLS / "visual-document-delivery" / "SKILL.md").read_text(encoding="utf-8")
        matrix_text = (SKILLS / "visual-document-delivery" / "references" / "visual-decision-matrix.md").read_text(encoding="utf-8")
        render_text = (SKILLS / "visual-document-delivery" / "references" / "render-and-acceptance.md").read_text(encoding="utf-8")
        for text in (visual_text, matrix_text, render_text):
            self.assertIn("目标格式", text)
            self.assertIn("no_visual_reason", text)
        self.assertIn("默认使用飞书原生画板", visual_text)
        self.assertIn("既有有效画板", visual_text)
        self.assertIn("原生节点", visual_text)
        self.assertIn("impeccable", visual_text)
        self.assertIn("画板块", render_text)
        self.assertIn("非飞书", visual_text)

    def test_discovery_metadata_keeps_the_three_core_routes_distinct(self):
        mock_ui = (SKILLS / "student-mock-interview-delivery" / "agents" / "openai.yaml").read_text(encoding="utf-8")
        recording = (SKILLS / "recording-processing" / "SKILL.md").read_text(encoding="utf-8")
        stories = (SKILLS / "building-resume-interview-stories" / "SKILL.md").read_text(encoding="utf-8")
        mock_contract = (SKILLS / "student-mock-interview-delivery" / "references" / "interview-content-contract.md").read_text(encoding="utf-8")

        self.assertIn("模拟面试", mock_ui)
        self.assertIn("student-interview-review-delivery", recording)
        self.assertIn("student-role-interview-prep", stories)
        self.assertIn("student-mock-interview-delivery", stories)
        self.assertNotIn("有真实公司与 JD 时才增加", mock_contract)

    def test_distributed_skills_do_not_embed_private_feishu_targets(self):
        text_suffixes = {".md", ".py", ".yaml", ".yml", ".json", ".toml", ".txt"}
        corpus = "\n".join(
            path.read_text(encoding="utf-8")
            for path in SKILLS.rglob("*")
            if path.is_file() and 'node_modules' not in path.parts and path.suffix in text_suffixes
        )
        self.assertIsNone(re.search(r"space_id`?:\s*`?\d{10,}", corpus))
        self.assertNotIn("旧分类父节点", corpus)
        self.assertNotIn("/" + "Users" + "/", corpus)

    def test_repository_does_not_embed_secret_like_values_or_private_feishu_urls(self):
        text_suffixes = {".md", ".py", ".yaml", ".yml", ".json", ".toml", ".txt"}
        files = [
            path
            for path in ROOT.rglob("*")
            if path.is_file() and ".git" not in path.parts and "node_modules" not in path.parts and path.suffix in text_suffixes
        ]
        corpus = "\n".join(path.read_text(encoding="utf-8") for path in files)
        forbidden = (
            r"sk-[A-Za-z0-9_-]{16,}",
            r"AKIA[0-9A-Z]{16}",
            r"gh[pousr]_[A-Za-z0-9]{20,}",
            r"xox[baprs]-[A-Za-z0-9-]{10,}",
            r"Bearer\s+[A-Za-z0-9._-]{20,}",
            r"\bou_[A-Za-z0-9]{16,}\b",
            r"\bcli_[A-Za-z0-9]{12,}\b",
            r"\b(?:tbl|rec)[A-Za-z0-9]{12,}\b",
            r"https://[^\s)]+(?:feishu\.cn|larksuite\.com)/(?:wiki|docx|docs|base|drive)/[^\s)]+",
        )
        for pattern in forbidden:
            self.assertIsNone(re.search(pattern, corpus, re.IGNORECASE), pattern)

    def test_repository_does_not_embed_absolute_user_paths(self):
        offenders = []
        for path in ROOT.rglob("*"):
            if not path.is_file() or ".git" in path.parts or "node_modules" in path.parts:
                continue
            if path.suffix not in {".md", ".py", ".yaml", ".yml", ".json", ".toml", ".txt"}:
                continue
            absolute_user_prefix = "/" + "Users" + "/"
            if absolute_user_prefix in path.read_text(encoding="utf-8"):
                offenders.append(str(path.relative_to(ROOT)))
        self.assertEqual([], offenders)

    def test_plugin_manifest_points_to_skills_directory(self):
        manifest = json.loads((ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
        self.assertEqual("codex-student-interview-skills", manifest["name"])
        self.assertEqual("./skills/", manifest["skills"])

        portable = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))
        self.assertEqual("https://agent-plugins.org/schemas/1.0.0/plugin.schema.json", portable["$schema"])
        self.assertEqual(manifest["name"], portable["name"])
        self.assertEqual(
            portable["extensions"]["com.openai"]["interface"]["capabilities"],
            manifest["interface"]["capabilities"],
        )

        marketplace = json.loads((ROOT / ".agents" / "plugins" / "marketplace.json").read_text(encoding="utf-8"))
        entry = marketplace["plugins"][0]
        self.assertEqual(portable["name"], entry["name"])
        self.assertEqual(
            "https://github.com/Amentman/campus-career-delivery.git",
            entry["source"]["url"],
        )

    def test_source_prompt_snapshots_are_present(self):
        manifest = json.loads((ROOT / "docs" / "SYNC_MANIFEST.json").read_text())
        expected = manifest["prompt_sha256"]
        for filename, digest in expected.items():
            content = (ROOT / "prompts" / filename).read_bytes()
            self.assertEqual(digest, hashlib.sha256(content).hexdigest())

    def test_synced_skill_trees_match_the_release_manifest(self):
        manifest = json.loads((ROOT / "docs" / "SYNC_MANIFEST.json").read_text())
        actual = {
            str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in SKILLS.rglob("*")
            if path.is_file() and "__pycache__" not in path.parts and "node_modules" not in path.parts and path.name != ".DS_Store" and path.suffix != ".pyc"
        }
        self.assertEqual(manifest["files_sha256"], actual)
        self.assertEqual(manifest["skill_count"], len(manifest["skills"]))
        self.assertEqual(set(manifest["skills"]), {path.name for path in SKILLS.iterdir() if (path / "SKILL.md").is_file()})


if __name__ == "__main__":
    unittest.main()
