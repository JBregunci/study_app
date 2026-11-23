from app.markdown_utils import render_markdown


def test_materials_list_and_detail(env):
    response = env.client.get("/materiais")
    assert response.status_code == 200
    assert "Materiais de estudo" in response.text
    assert "Macroeconomia" in response.text

    response = env.client.get("/materiais/macroeconomia-visao-geral")
    assert response.status_code == 200
    assert "Macroeconomia: contas nacionais, modelos e política" in response.text
    assert "Questões relacionadas" in response.text
    assert "Questões do tema" in response.text
    assert "Material gerado" in response.text


def test_materials_filter_by_topic(env):
    response = env.client.get("/materiais?tema=portugues")
    assert response.status_code == 200
    assert "Interpretação de textos" in response.text
    assert "Crase, concordância e pontuação" in response.text


def test_markdown_is_sanitized():
    html = render_markdown("**ok** <script>alert('x')</script> [link](https://example.com)")
    assert "<strong>ok</strong>" in html
    assert "<script" not in html
    assert 'href="https://example.com"' in html
