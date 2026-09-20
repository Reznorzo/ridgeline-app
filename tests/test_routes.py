import asyncio
import io
import tempfile
import unittest
from pathlib import Path

from starlette.datastructures import UploadFile

from app import database
from app.routers.routes import import_gpx
from tests.test_gpx import SIMPLE_GPX


class RoutesTest(unittest.TestCase):
    def test_import_gpx_accepts_upload_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            database.DB_PATH = str(Path(temp_dir) / "ridgeline.db")
            if database.conn is not None:
                database.conn.close()
            database.conn = None
            database.init_db()

            upload = UploadFile(io.BytesIO(SIMPLE_GPX), filename="helvellyn.gpx")
            result = asyncio.run(import_gpx(upload))

            self.assertEqual(result.name, "helvellyn")
            self.assertGreater(result.distance_km, 0)
            self.assertEqual(result.ascent_m, 25)

            row = database.get_connection().execute("SELECT name FROM routes WHERE id = ?", (result.id,)).fetchone()
            self.assertEqual(row["name"], "helvellyn")


if __name__ == "__main__":
    unittest.main()
