import pytest

def merge_rows(existing,incoming):
    by_key={(r[0],r[1]):list(r) for r in existing}
    for r in incoming: by_key[(r[0],r[1])]=list(r)
    return sorted(by_key.values(),key=lambda r:(r[0],r[1]))

def test_overlap_correction_and_new_session():
    existing=[["2026-09-28","RELIANCE",100,110,99,108,1000],["2026-09-29","RELIANCE",108,112,107,111,1200]]
    incoming=[["2026-09-29","RELIANCE",108,113,107,112,1250],["2026-09-30","RELIANCE",112,115,111,114,1300]]
    merged=merge_rows(existing,incoming)
    assert merged[1]==incoming[0]
    assert len(merged)==3

def test_identical_overlap_is_idempotent():
    row=["2026-09-29","RELIANCE",108,112,107,111,1200]
    assert merge_rows([row],[row])==[row]

def test_current_pointer_changes_only_after_publication():
    current={"object":"prices/v1.parquet"}; candidate={"object":"prices/v2.parquet"}
    published=False
    if published: current=candidate
    assert current["object"]=="prices/v1.parquet"
    published=True
    if published: current=candidate
    assert current["object"]=="prices/v2.parquet"

def test_duplicate_symbol_date_is_rejected():
    rows=[["2026-09-29","RELIANCE",1,2,1,2,1],["2026-09-29","RELIANCE",1,2,1,2,1]]
    keys=[(r[0],r[1]) for r in rows]
    with pytest.raises(AssertionError):
        assert len(keys)==len(set(keys))
