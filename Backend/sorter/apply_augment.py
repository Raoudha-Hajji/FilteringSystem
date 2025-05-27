from sorter.augment import augment_sqlite_with_translations

augment_sqlite_with_translations(
    db_path='db.sqlite3',
    table_name='Tuneps',
    text_column='Intitulé du projet'  # or whatever column needs translation
)

