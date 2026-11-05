"""A team installation must include readable, portable workflow figures."""
import hashlib
from pathlib import Path
import re
import unittest
import xml.etree.ElementTree as ET
from scripts.sync_public import private_reason

ROOT=Path(__file__).resolve().parents[1]
class SkillWorkflowTests(unittest.TestCase):
    def test_every_shipped_skill_links_a_complete_guide_and_nonempty_svg(self):
        for folder in (ROOT/'skills').iterdir():
            if not (folder/'SKILL.md').is_file():continue
            with self.subTest(skill=folder.name):
                self.assertIn('(references/workflow.md)',(folder/'SKILL.md').read_text())
                guide=folder/'references/workflow.md'
                content=guide.read_text()
                pictures=re.findall(r'!\[[^\]]*\]\(([^)]+)\)',content)
                self.assertTrue(pictures)
                self.assertIn('../assets/input-confirmation.svg',pictures,'input questions must have their own readable diagram')
                self.assertIn('../assets/workflow.svg',pictures,'the execution diagram remains part of the same guide')
                self.assertIn('flowchart ',content,'editable source is part of the guide')
                for picture in pictures:
                    path=(guide.parent/picture).resolve()
                    self.assertTrue(path.is_relative_to(folder.resolve()))
                    svg=path.read_text();self.assertIsNone(private_reason(svg),path)
                    figure=ET.fromstring(svg)
                    self.assertEqual(figure.tag,'{http://www.w3.org/2000/svg}svg')
                    self.assertTrue(figure.find('{http://www.w3.org/2000/svg}title').text)
                    self.assertNotIn('<script',svg.lower())
                    self.assertNotRegex(svg,r'(?:href|src)="https?://')
                    seal=re.search(r' data-artifact-sha256="([a-f0-9]{64})"',svg)
                    self.assertIsNotNone(seal)
                    original=svg[:seal.start()]+svg[seal.end():]
                    self.assertEqual(hashlib.sha256(original.encode()).hexdigest(),seal[1])

    def test_two_job_write_destinations_and_recovery_are_explained_together(self):
        guide=(ROOT/'skills/campus-job-matching/references/workflow.md').read_text()
        self.assertIn('原投递表',guide)
        self.assertIn('共享岗位库',guide)
        self.assertIn('回收失败',guide)
        self.assertIn('默认视图',guide)
        self.assertIn('pending',guide)
