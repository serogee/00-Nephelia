import db

conn = db.connect("database/settings.db")
cur = conn.cursor()
cur.execute("""
    SELECT server_id, bot_prefix FROM server_settings
""")

default_prefix = "&"
cached_prefix = {id: pref for id, pref in cur.fetchall() if pref is not None}


def set_default(prefix: str):
    global default_prefix
    default_prefix = prefix

def get_prefix(message):
    if (mgid := message.guild.id) in cached_prefix:
        return cached_prefix[mgid]
    return default_prefix

def set_prefix(guild_id, prefix: str):
    if prefix == default_prefix:
        prefix = None

    cur.execute("""
        UPDATE server_settings 
        SET bot_prefix=?
        WHERE guild_id=?
    """, (prefix, guild_id))
    cur.execute("""
        INSERT OR IGNORE INTO server_settings (prefix)
        VALUES (?)
    """, (prefix,))
    
    if prefix is None:
        del cached_prefix[guild_id]
    else:
        cached_prefix[guild_id] = prefix