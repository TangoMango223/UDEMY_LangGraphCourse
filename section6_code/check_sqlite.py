# #  Imports
# import sqlite3

# # Initialize connection
# conn = sqlite3.connect("data/checkpoints.sqlite")
# cursor = conn.cursor()

# # First, let's see what tables exist
# cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
# print("Tables in database:", cursor.fetchall())

# # Then, let's see the table structure (if checkpoints table exists)
# cursor.execute("PRAGMA table_info(checkpoints);")
# print("\nTable structure:", cursor.fetchall())

# # Finally, let's see all records
# cursor.execute("SELECT * FROM checkpoints;")
# print("\nAll records:", cursor.fetchall())

# # Delete the table contents, but keep the table
# cursor.execute("DELETE FROM checkpoints")
# conn.commit()


# # Delete also deletes the table:
# cursor.execute("DELETE TABLE checkpoints")

import sqlite3
import msgpack  # You might need to install this: pip install msgpack

conn = sqlite3.connect("data/checkpoints.sqlite")
cursor = conn.cursor()

# Let's see the structure of the writes table
cursor.execute("PRAGMA table_info(writes);")
print("\nWrites table structure:", cursor.fetchall())

# And see what's in it
cursor.execute("SELECT * FROM writes;")
print("\nWrites table contents:", cursor.fetchall())


# Get the writes with decoded values
cursor.execute("SELECT thread_id, channel, type, value FROM writes")
for row in cursor.fetchall():
    thread_id, channel, type_, value = row
    if type_ == 'msgpack':
        try:
            decoded_value = msgpack.unpackb(bytes.fromhex(value[2:]))  # Remove 'a6' prefix and decode
            print(f"Channel: {channel}, Value: {decoded_value}")
        except Exception as e:
            print(f"Could not decode {value}: {e}")

# It's under the "Write" column
# But under "values", it is all encoded as hex-encoded.
# The value part will say things like what was written