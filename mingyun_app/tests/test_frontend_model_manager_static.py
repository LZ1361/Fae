from pathlib import Path
import unittest


STATIC_DIR = Path(__file__).resolve().parents[1] / "static"
PROJECT_DIR = Path(__file__).resolve().parents[2]


class FrontendModelManagerStaticTests(unittest.TestCase):
    def test_model_manager_page_contains_expected_controls(self):
        html = (STATIC_DIR / "models.html").read_text(encoding="utf-8")

        self.assertIn('name="param_overrides"', html)
        self.assertIn('id="modelList"', html)
        self.assertIn("saveLocalModelBtn", html)

    def test_main_page_keeps_model_management_separate(self):
        html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")

        self.assertIn('href="/models.html"', html)
        self.assertNotIn('id="modelConfigForm"', html)

    def test_model_manager_script_exposes_card_actions(self):
        script = (STATIC_DIR / "app.js").read_text(encoding="utf-8")

        self.assertIn("cloneModel", script)
        self.assertIn("toggleModelEnabled", script)
        self.assertIn("testModelConfig", script)
        self.assertIn("parseParamOverrides", script)

    def test_main_report_script_renders_rich_bazi_sections(self):
        script = (STATIC_DIR / "app.js").read_text(encoding="utf-8")
        css = (STATIC_DIR / "styles.css").read_text(encoding="utf-8")

        self.assertIn("renderChartOverview", script)
        self.assertIn("renderLifeTopics", script)
        self.assertIn("renderDerivedFacts", script)
        self.assertIn("questions_to_reflect", script)
        self.assertIn(".chart-overview", css)
        self.assertIn(".life-topic-grid", css)

    def test_main_page_persists_form_and_supports_lunar_inputs(self):
        html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
        script = (STATIC_DIR / "app.js").read_text(encoding="utf-8")

        self.assertIn('name="calendar_type"', html)
        self.assertIn('value="lunar"', html)
        self.assertIn('name="lunar_is_leap"', html)
        self.assertIn("STORAGE_READING_DRAFT", script)
        self.assertIn("restoreReadingDraft", script)
        self.assertIn("saveReadingDraft", script)

    def test_model_page_exposes_save_config_and_test_autosave(self):
        html = (STATIC_DIR / "models.html").read_text(encoding="utf-8")
        script = (STATIC_DIR / "app.js").read_text(encoding="utf-8")

        self.assertIn("保存配置/API", html)
        self.assertIn("saveCurrentModelConfig", script)
        self.assertIn("persistModelConfig", script)
        self.assertIn("autoSaveOnTestSuccess", script)

    def test_main_report_script_renders_relationship_and_matchmaking(self):
        script = (STATIC_DIR / "app.js").read_text(encoding="utf-8")
        css = (STATIC_DIR / "styles.css").read_text(encoding="utf-8")

        self.assertIn("renderRelationshipProfile", script)
        self.assertIn("renderMatchmaking", script)
        self.assertIn(".matchmaking-panel", css)

    def test_visual_polish_assets_and_interactions_exist(self):
        html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
        models_html = (STATIC_DIR / "models.html").read_text(encoding="utf-8")
        script = (STATIC_DIR / "app.js").read_text(encoding="utf-8")
        css = (STATIC_DIR / "styles.css").read_text(encoding="utf-8")

        self.assertTrue((STATIC_DIR / "assets" / "mingyun-paper-cosmos.png").exists())
        self.assertTrue((STATIC_DIR / "assets" / "mingyun-starry-sky.png").exists())
        self.assertTrue((STATIC_DIR / "assets" / "mingyun-commercial-starry-bg.png").exists())
        self.assertTrue((STATIC_DIR / "assets" / "mingyun-astrolabe-wheel.png").exists())
        self.assertTrue((STATIC_DIR / "assets" / "mingyun-fate-mark.png").exists())
        self.assertTrue((STATIC_DIR / "assets" / "mingyun-destiny-icon.png").exists())
        self.assertTrue((STATIC_DIR / "assets" / "mingyun-destiny-icon.ico").exists())
        self.assertTrue((STATIC_DIR / "favicon.ico").exists())
        self.assertIn("app-backdrop", html)
        self.assertIn("创作者：不做梵高", html)
        self.assertIn("创作者：不做梵高", models_html)
        self.assertNotIn("把玄学表达收束到可复核依据里。", html)
        self.assertIn("rotating-astrolabe", html)
        self.assertIn("mingyun-destiny-icon.png", html)
        self.assertIn("/favicon.ico", html)
        self.assertIn("toastStack", html)
        self.assertIn("app-backdrop", models_html)
        self.assertIn("rotating-astrolabe", models_html)
        self.assertIn("mingyun-destiny-icon.png", models_html)
        self.assertIn("/favicon.ico", models_html)
        self.assertIn("toastStack", models_html)
        self.assertIn("installClickSymbols", script)
        self.assertIn("showToast", script)
        self.assertIn("click-star", script)
        self.assertIn("document.addEventListener(\"pointerdown\"", script)
        self.assertIn("starCount = 7", script)
        self.assertIn("click-symbol", css)
        self.assertIn("click-star", css)
        self.assertIn("mingyun-commercial-starry-bg.png", css)
        self.assertIn("1500ms", css)
        self.assertIn("hero-creator", css)
        self.assertIn("rotating-astrolabe", css)
        self.assertIn("astrolabeSpin", css)
        self.assertIn("toast-stack", css)
        self.assertIn("premium-panel", css)

    def test_brand_is_top_left_and_creator_sits_above_hero_eyebrow(self):
        html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
        models_html = (STATIC_DIR / "models.html").read_text(encoding="utf-8")
        css = (STATIC_DIR / "styles.css").read_text(encoding="utf-8")

        self.assertTrue((STATIC_DIR / "assets" / "mingyun-destiny-icon.png").exists())
        self.assertIn("brand-lockup", html)
        self.assertIn("brand-lockup", models_html)
        self.assertNotIn("brand-centerline", html)
        self.assertNotIn("brand-centerline", models_html)
        self.assertIn("brand-title", html)
        self.assertIn("hero-creator", html)
        self.assertLess(html.index("hero-creator"), html.index("真实推断，不迎合情绪"))
        self.assertIn("mingyun-destiny-icon.png", html)
        self.assertIn("mingyun-destiny-icon.png", models_html)
        self.assertNotIn("mingyun-fate-mark.png", html)
        self.assertNotIn("mingyun-fate-mark.png", models_html)
        self.assertNotIn("mingyun-reincarnation-mark.png", html)
        self.assertNotIn("mingyun-reincarnation-mark.png", models_html)
        self.assertIn(".brand-lockup", css)
        self.assertNotIn("left: 50%;", css)
        self.assertNotIn("transform: translateX(-50%);", css)
        self.assertIn("font-size: clamp(26px, 2.5vw, 34px);", css)

    def test_main_form_keeps_gender_only_without_reference_tone(self):
        html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")

        self.assertIn("性别", html)
        self.assertIn('<option value="female">女</option>', html)
        self.assertIn('<option value="male">男</option>', html)
        self.assertNotIn("性别/参照口径", html)
        self.assertNotIn("女性传统口径", html)
        self.assertNotIn("男性传统口径", html)

    def test_surfaces_are_translucent_and_small_text_is_larger(self):
        css = (STATIC_DIR / "styles.css").read_text(encoding="utf-8")

        self.assertIn("--surface: rgba(13, 21, 38, 0.18);", css)
        self.assertIn("--surface-2: rgba(20, 31, 54, 0.24);", css)
        self.assertIn("--field: rgba(7, 13, 28, 0.24);", css)
        self.assertIn("linear-gradient(180deg, rgba(19, 29, 52, 0.08), rgba(10, 17, 32, 0.02))", css)
        self.assertIn("background: rgba(10, 17, 32, 0.16);", css)
        self.assertIn("backdrop-filter: blur(6px) saturate(1.12);", css)
        self.assertIn("font-size: 16px;", css)
        self.assertNotIn("font-size: 11px;", css)

    def test_rotating_astrolabe_is_a_visible_global_background_layer(self):
        css = (STATIC_DIR / "styles.css").read_text(encoding="utf-8")

        self.assertIn(".app-backdrop::before", css)
        self.assertIn('background: url("/assets/mingyun-astrolabe-wheel.png") center / min(1380px, 108vw) no-repeat;', css)
        self.assertIn("animation: astrolabeSpin 140s linear infinite reverse;", css)
        self.assertIn("opacity: 0.38;", css)
        self.assertIn("opacity: 0.5;", css)
        self.assertIn("contrast(1.28) brightness(1.38) saturate(1.12)", css)

    def test_model_manager_heading_is_more_compact(self):
        css = (STATIC_DIR / "styles.css").read_text(encoding="utf-8")

        self.assertIn(".models-page h1", css)
        self.assertIn("font-size: clamp(32px, 4.5vw, 56px);", css)

    def test_report_text_uses_symbolized_reading_layout(self):
        script = (STATIC_DIR / "app.js").read_text(encoding="utf-8")
        css = (STATIC_DIR / "styles.css").read_text(encoding="utf-8")

        self.assertIn("renderPlainTakeaways", script)
        self.assertIn("plain_takeaways", script)
        self.assertIn("dimension-symbol", script)
        self.assertIn("basis-list", script)
        self.assertIn("suggestion-list", script)
        self.assertIn("topic-symbol", script)
        self.assertIn("readingSymbols", script)
        self.assertIn(".plain-takeaways", css)
        self.assertIn(".dimension-heading", css)
        self.assertIn(".dimension-symbol", css)
        self.assertIn(".basis-list", css)
        self.assertIn(".suggestion-list", css)

    def test_windows_packaging_and_github_release_files_exist(self):
        build_script = PROJECT_DIR / "scripts" / "build_windows.ps1"
        workflow = PROJECT_DIR / ".github" / "workflows" / "windows-build.yml"
        packaging_doc = PROJECT_DIR / "docs" / "PACKAGING.md"
        license_file = PROJECT_DIR / "LICENSE"
        requirements = PROJECT_DIR / "requirements-build.txt"

        self.assertTrue(build_script.exists())
        self.assertTrue(workflow.exists())
        self.assertTrue(packaging_doc.exists())
        self.assertTrue(license_file.exists())
        self.assertTrue(requirements.exists())
        self.assertIn("PyInstaller", build_script.read_text(encoding="utf-8"))
        self.assertIn("mingyun_app/app.py", build_script.read_text(encoding="utf-8"))
        self.assertIn("actions/upload-artifact", workflow.read_text(encoding="utf-8"))

    def test_api_keys_remain_browser_local_and_are_not_bundled(self):
        script = (STATIC_DIR / "app.js").read_text(encoding="utf-8")
        docs = [
            (PROJECT_DIR / "18_产品售卖交付与合规方案.md").read_text(encoding="utf-8"),
            (PROJECT_DIR / "mingyun_app" / "README.md").read_text(encoding="utf-8"),
        ]

        self.assertIn('const STORAGE_KEYS = "mingyun.apiKeys";', script)
        self.assertIn("localStorage.setItem(STORAGE_KEYS", script)
        self.assertIn("localStorage.removeItem(STORAGE_KEYS)", script)
        self.assertTrue(any("不会随软件交付给客户" in doc for doc in docs))

    def test_customer_delivery_document_exists(self):
        doc = PROJECT_DIR / "18_产品售卖交付与合规方案.md"

        self.assertTrue(doc.exists())
        text = doc.read_text(encoding="utf-8")
        self.assertIn("Windows 本地版", text)
        self.assertIn("客户自行配置 API Key", text)
        self.assertIn("隐私政策", text)
        self.assertIn("AI 生成，仅供参考", text)


if __name__ == "__main__":
    unittest.main()
