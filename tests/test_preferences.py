import sqlite3

from ctk_tb.model import preferences as pref


def _create_preferences_db(db_path):
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        create table preferences (
            scope text not null,
            preference_name text not null,
            data_type text not null,
            preference_value text,
            preference_label text,
            preference_attr1 text,
            preference_attr2 text,
            preference_attr3 text,
            preference_attr4 text,
            preference_attr5 text
        );
        """
    )
    conn.commit()
    conn.close()


def test_upsert_preference_inserts_and_updates(tmp_path):
    db_path = tmp_path / "preferences.db"
    _create_preferences_db(db_path)

    row = pref.new_preference_dict(
        scope="scaling",
        preference_name="icon_browser",
        data_type="str",
        preference_value="100%",
    )
    pref.upsert_preference(db_file_path=db_path, preference_row_dict=row)

    assert pref.preference_setting(db_file_path=db_path, scope="scaling", preference_name="icon_browser") == "100%"

    row["preference_value"] = "70%"
    pref.upsert_preference(db_file_path=db_path, preference_row_dict=row)

    assert pref.preference_setting(db_file_path=db_path, scope="scaling", preference_name="icon_browser") == "70%"


def test_preference_setting_returns_default_when_row_missing(tmp_path):
    db_path = tmp_path / "preferences.db"
    _create_preferences_db(db_path)

    assert pref.preference_setting(
        db_file_path=db_path,
        scope="window_geometry",
        preference_name="icon_browser",
        default="1040x680+120+80",
    ) == "1040x680+120+80"
