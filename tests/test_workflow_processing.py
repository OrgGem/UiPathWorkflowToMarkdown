from io import BytesIO
from zipfile import ZipFile

from fastapi.testclient import TestClient

from app.llm import enrich_with_llm
from app.main import app
from app.markdown_gen import build_markdown
from app.parser import WorkflowData, parse_project


SAMPLE_XAML = """<?xml version=\"1.0\" encoding=\"utf-8\"?>
<Activity mc:Ignorable=\"sap sap2010\" x:Class=\"Main\" xmlns=\"http://schemas.microsoft.com/netfx/2009/xaml/activities\" xmlns:mc=\"http://schemas.openxmlformats.org/markup-compatibility/2006\" xmlns:mva=\"clr-namespace:Microsoft.VisualBasic.Activities;assembly=System.Activities\" xmlns:s=\"clr-namespace:System;assembly=mscorlib\" xmlns:s1=\"clr-namespace:System;assembly=System\" xmlns:scg=\"clr-namespace:System.Collections.Generic;assembly=System\" xmlns:sco=\"clr-namespace:System.Collections.ObjectModel;assembly=mscorlib\" xmlns:ui=\"http://schemas.uipath.com/workflow/activities\" xmlns:x=\"http://schemas.microsoft.com/winfx/2006/xaml\">
  <Sequence DisplayName=\"Main Sequence\">
    <ui:InvokeWorkflowFile DisplayName=\"Call Child\" WorkflowFileName=\"Child.xaml\" />
    <ui:Click DisplayName=\"Click Button\" />
  </Sequence>
</Activity>
"""

CHILD_XAML = """<?xml version=\"1.0\" encoding=\"utf-8\"?>
<Activity x:Class=\"Child\" xmlns=\"http://schemas.microsoft.com/netfx/2009/xaml/activities\" xmlns:ui=\"http://schemas.uipath.com/workflow/activities\" xmlns:x=\"http://schemas.microsoft.com/winfx/2006/xaml\">
  <Sequence DisplayName=\"Child Sequence\">
    <ui:TypeInto DisplayName=\"Type Hello\" />
  </Sequence>
</Activity>
"""

NESTED_XAML = """<?xml version=\"1.0\" encoding=\"utf-8\"?>
<Activity x:Class=\"Login\" xmlns=\"http://schemas.microsoft.com/netfx/2009/xaml/activities\" xmlns:ui=\"http://schemas.uipath.com/workflow/activities\" xmlns:x=\"http://schemas.microsoft.com/winfx/2006/xaml\">
  <Sequence DisplayName=\"Login Flow\">
    <If DisplayName=\"Check Login Success\">
      <If.Then>
        <Sequence DisplayName=\"Success Branch\">
          <ui:Click DisplayName=\"Open Dashboard\" />
        </Sequence>
      </If.Then>
      <If.Else>
        <Sequence DisplayName=\"Retry Branch\">
          <ui:InvokeWorkflowFile DisplayName=\"Retry Login\" WorkflowFileName=\"Retry.xaml\" />
        </Sequence>
      </If.Else>
    </If>
  </Sequence>
</Activity>
"""


def _build_zip() -> BytesIO:
    buf = BytesIO()
    with ZipFile(buf, "w") as zf:
        zf.writestr("Main.xaml", SAMPLE_XAML)
        zf.writestr("Child.xaml", CHILD_XAML)
    buf.seek(0)
    return buf


def test_build_markdown_includes_llm_summary():
    workflows = {
        "Main.xaml": WorkflowData(
            path="Main.xaml",
            display_name="Main",
            invoked_workflows=["Child.xaml"],
            key_activities=["Main Sequence", "Click Button"],
        ),
        "Child.xaml": WorkflowData(
            path="Child.xaml",
            display_name="Child",
            invoked_workflows=[],
            key_activities=["Type Hello"],
        ),
    }
    llm_descriptions = {"Main.xaml": "Handles the main flow."}

    markdown = build_markdown(workflows, llm_descriptions)
    assert "Handles the main flow." in markdown
    assert "Child.xaml" in markdown
    assert "Key activities" in markdown


def test_enrich_with_llm_returns_empty_when_disabled():
    workflows = {}
    result = enrich_with_llm(workflows, {"use_llm": False})
    assert result == {}


def test_upload_endpoint_processes_zip():
    client = TestClient(app)
    archive = _build_zip()
    files = {"file": ("project.zip", archive, "application/zip")}
    response = client.post("/analyze/upload/", files=files)
    assert response.status_code == 200
    assert "UiPath Project Summary" in response.text
    assert "Main.xaml" in response.text


def test_markdown_includes_nested_logic_flow(tmp_path):
    xaml_path = tmp_path / "Login.xaml"
    xaml_path.write_text(NESTED_XAML, encoding="utf-8")

    workflows = parse_project(tmp_path)
    markdown = build_markdown(workflows)

    assert "Logic flow" in markdown
    assert "Login Flow [Sequence]" in markdown
    assert "Check Login Success [If]" in markdown
    assert "Then: Success Branch [Sequence]" in markdown
    assert "Else: Retry Branch [Sequence]" in markdown
    assert "Retry Login [InvokeWorkflowFile]" in markdown
