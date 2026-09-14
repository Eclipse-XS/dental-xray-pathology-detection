from dental_xray_service.models.metadata import sha256_file


def test_artifact_checksum_is_deterministic(tmp_path):
    artifact = tmp_path / "artifact.bin"
    artifact.write_bytes(b"dentex")
    assert sha256_file(artifact) == "4a20c92465f40133838503af40ee70486ff34fb5dc3a6aa1186ca78e63008334"
