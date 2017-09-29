import os
import unittest

from .helpers.cfs_helpers import find_by_extensions, find_by_name
from .helpers.ptrack_helpers import ProbackupTest, ProbackupException

module_name = 'cfs_backup_noenc'
tblspace_name = 'cfs_tblspace'


class CfsBackupEncTest(ProbackupTest, unittest.TestCase):
    fname = None
    backup_dir = None
    node = None

# --- Begin --- #
    def setUp(self):
        global fname
        global backup_dir
        global node

        os.environ["PG_CIPHER_KEY"] = "super_secret_cipher_key"

        fname = self.id().split('.')[3]
        backup_dir = os.path.join(self.tmp_path, module_name, fname, 'backup')

        node = self.make_simple_node(
            base_dir="{0}/{1}/node".format(module_name, fname),
            set_replication=True,
            initdb_params=['--data-checksums'],
            pg_options={
                'wal_level': 'replica',
                'ptrack_enable': 'on',
                'cfs_encryption': 'on',
                'max_wal_senders': '2'
            }
        )

        self.init_pb(backup_dir)
        self.add_instance(backup_dir, 'node', node)
        self.set_archiving(backup_dir, 'node', node)

        node.start()

        self.create_tblspace_in_node(node, tblspace_name, True)
        
        tblspace = node.safe_psql(
            "postgres",
            "SELECT * FROM pg_tablespace WHERE spcname='{0}'".format(tblspace_name)
        )
        self.assertTrue(
            tblspace_name in tblspace and "compression=true" in tblspace,
            "ERROR: The tablespace not created or it create without compressions"
        )

        self.assertTrue(
            find_by_name([self.get_tblspace_path(node, tblspace_name)], ['pg_compression']),
            "ERROR: File pg_compression not found"
        )

# --- Section: Full --- #
    # @unittest.expectedFailure
    # @unittest.skip("skip")
    def test_fullbackup_empty_tablespace(self):
        """
        Case: Check fullbackup empty compressed tablespace
        """

        backup_id = None
        try:
            backup_id = self.backup_node(backup_dir, 'node', node, backup_type='full')
        except ProbackupException as e:
            self.assertTrue(
                False,
                "ERROR: Full backup failed.\n {0} \n {1}".format(
                    repr(self.cmd),
                    repr(e.message)
                )
            )
        show_backup = self.show_pb(backup_dir, 'node', backup_id)
        self.assertEqual(
            "OK",
            show_backup["status"],
            "ERROR: Full backup status is not valid. \n Current backup status={0}".format(show_backup["status"])
        )
        self.assertTrue(
            find_by_name([os.path.join(backup_dir, 'backups', 'node', backup_id)], ['pg_compression']),
            "ERROR: File pg_compression not found in backup dir"
        )

    # @unittest.expectedFailure
    # @unittest.skip("skip")
    def test_fullbackup_empty_tablespace_stream(self):
        """
        Case: Check fullbackup empty compressed tablespace with options stream
        """

        backup_id = None
        try:
            backup_id = self.backup_node(backup_dir, 'node', node, backup_type='full', options=['--stream'])
        except ProbackupException as e:
            self.assertTrue(
                False,
                "ERROR: Full backup failed.\n {0} \n {1}".format(
                    repr(self.cmd),
                    repr(e.message)
                )
            )
        show_backup = self.show_pb(backup_dir, 'node', backup_id)
        self.assertEqual(
            "OK",
            show_backup["status"],
            "ERROR: Full backup status is not valid. \n Current backup status={0}".format(show_backup["status"])
        )
        self.assertTrue(
            find_by_name([os.path.join(backup_dir, 'backups', 'node', backup_id)], ['pg_compression']),
            "ERROR: File pg_compression not found in backup dir"
        )
        self.assertFalse(
            find_by_extensions([os.path.join(backup_dir, 'node', backup_id)], ['_ptrack']),
            "ERROR: _ptrack files found in backup dir"
        )

    # @unittest.expectedFailure
    # @unittest.skip("skip")
    # PGPRO-1018 invalid file size
    def test_fullbackup_after_create_table(self):
        """
        Case: Make full backup after created table in the tablespace
        """

        node.safe_psql(
            "postgres",
            'CREATE TABLE {0} TABLESPACE {1} \
                AS SELECT i AS id, MD5(i::text) AS text, \
                MD5(repeat(i::text,10))::tsvector AS tsvector \
                FROM generate_series(0,256) i'.format('t1', tblspace_name)
        )

        backup_id = None
        try:
            backup_id = self.backup_node(backup_dir, 'node', node, backup_type='full')
        except ProbackupException as e:
            self.assertTrue(
                False,
                "ERROR: Full backup failed.\n {0} \n {0}".format(
                    repr(self.cmd),
                    repr(e.message)
                )
            )
        show_backup = self.show_pb(backup_dir, 'node', backup_id)
        self.assertEqual(
            "OK",
            show_backup["status"],
            "ERROR: Full backup status is not valid. \n Current backup status={0}".format(show_backup["status"])
        )
        self.assertTrue(
            find_by_name([os.path.join(backup_dir, 'backups', 'node', backup_id)], ['pg_compression']),
            "ERROR: File pg_compression not found in backup dir"
        )
        self.assertTrue(
            find_by_extensions([os.path.join(backup_dir, 'node', backup_id)], ['.cmf']),
            "ERROR: .cmf files not found in backup dir"
        )
        self.assertFalse(
            find_by_extensions([os.path.join(backup_dir, 'node', backup_id)], ['_ptrack']),
            "ERROR: _ptrack files was found in backup dir"
        )

    # @unittest.expectedFailure
    # @unittest.skip("skip")
    # PGPRO-1018 invalid file size
    def test_fullbackup_after_create_table_stream(self):
        """
        Case: Make full backup after created table in the tablespace with option --stream
        """

        node.safe_psql(
            "postgres",
            'CREATE TABLE {0} TABLESPACE {1} \
                AS SELECT i AS id, MD5(i::text) AS text, \
                MD5(repeat(i::text,10))::tsvector AS tsvector \
                FROM generate_series(0,256) i'.format('t1', tblspace_name)
        )

        backup_id = None
        try:
            backup_id = self.backup_node(backup_dir, 'node', node, backup_type='full', options=['--stream'])
        except ProbackupException as e:
            self.fail(
                "ERROR: Full backup failed.\n {0} \n {1}".format(
                    repr(self.cmd),
                    repr(e.message)
                )
            )
        show_backup = self.show_pb(backup_dir, 'node', backup_id)
        self.assertEqual(
            "OK",
            show_backup["status"],
            "ERROR: Full backup status is not valid. \n Current backup status={0}".format(show_backup["status"])
        )
        self.assertTrue(
            find_by_name([os.path.join(backup_dir, 'backups', 'node', backup_id)], ['pg_compression']),
            "ERROR: File pg_compression not found in backup dir"
        )
        self.assertTrue(
            find_by_extensions([os.path.join(backup_dir, 'node', backup_id)], ['.cmf']),
            "ERROR: .cmf files not found in backup dir"
        )
        self.assertFalse(
            find_by_extensions([os.path.join(backup_dir, 'node', backup_id)], ['_ptrack']),
            "ERROR: _ptrack files was found in backup dir"
        )

# --- Section: Incremental from empty tablespace --- #
    # @unittest.expectedFailure
    # @unittest.skip("skip")
    def test_fullbackup_empty_tablespace_ptrack_after_create_table(self):
        """
        Case: Make full backup before created table in the tablespace.
                Make ptrack backup after create table
        """

        try:
            self.backup_node(backup_dir, 'node', node, backup_type='full')
        except ProbackupException as e:
            self.assertTrue(
                False,
                "ERROR: Full backup failed.\n {0} \n {1}".format(
                    repr(self.cmd),
                    repr(e.message)
                )
            )

        node.safe_psql(
            "postgres",
            'CREATE TABLE {0} TABLESPACE {1} \
                AS SELECT i AS id, MD5(i::text) AS text, \
                MD5(repeat(i::text,10))::tsvector AS tsvector \
                FROM generate_series(0,256) i'.format('t1', tblspace_name)
        )

        backup_id = None
        try:
            backup_id = self.backup_node(backup_dir, 'node', node, backup_type='ptrack')
        except ProbackupException as e:
            self.assertTrue(
                False,
                "ERROR: Incremental backup failed.\n {0} \n {1}".format(
                    repr(self.cmd),
                    repr(e.message)
                )
            )
        show_backup = self.show_pb(backup_dir, 'node', backup_id)
        self.assertEqual(
            "OK",
            show_backup["status"],
            "ERROR: Incremental backup status is not valid. \n Current backup status={0}".format(show_backup["status"])
        )
        self.assertTrue(
            find_by_name([self.get_tblspace_path(node, tblspace_name)], ['pg_compression']),
            "ERROR: File pg_compression not found"
        )
        self.assertTrue(
            find_by_extensions([os.path.join(backup_dir, 'node', backup_id)], ['.cmf']),
            "ERROR: .cmf files not found in backup dir"
        )
        self.assertFalse(
            find_by_extensions([os.path.join(backup_dir, 'node', backup_id)], ['_ptrack']),
            "ERROR: _ptrack files was found in backup dir"
        )

    # @unittest.expectedFailure
    # @unittest.skip("skip")
    def test_fullbackup_empty_tablespace_ptrack_after_create_table_stream(self):
        """
        Case: Make full backup before created table in the tablespace.
                Make ptrack backup after create table
        """

        try:
            self.backup_node(backup_dir, 'node', node, backup_type='full', options=['--stream'])
        except ProbackupException as e:
            self.assertTrue(
                False,
                "ERROR: Full backup failed.\n {0} \n {1}".format(
                    repr(self.cmd),
                    repr(e.message)
                )
            )

        node.safe_psql(
            "postgres",
            'CREATE TABLE {0} TABLESPACE {1} \
                AS SELECT i AS id, MD5(i::text) AS text, \
                MD5(repeat(i::text,10))::tsvector AS tsvector \
                FROM generate_series(0,256) i'.format('t1', tblspace_name)
        )

        backup_id = None
        try:
            backup_id = self.backup_node(backup_dir, 'node', node, backup_type='ptrack', options=['--stream'])
        except ProbackupException as e:
            self.assertTrue(
                False,
                "ERROR: Incremental backup failed.\n {0} \n {1}".format(
                    repr(self.cmd),
                    repr(e.message)
                )
            )
        show_backup = self.show_pb(backup_dir, 'node', backup_id)
        self.assertEqual(
            "OK",
            show_backup["status"],
            "ERROR: Incremental backup status is not valid. \n Current backup status={0}".format(show_backup["status"])
        )
        self.assertTrue(
            find_by_name([self.get_tblspace_path(node, tblspace_name)], ['pg_compression']),
            "ERROR: File pg_compression not found"
        )
        self.assertTrue(
            find_by_extensions([os.path.join(backup_dir, 'node', backup_id)], ['.cmf']),
            "ERROR: .cmf files not found in backup dir"
        )
        self.assertFalse(
            find_by_extensions([os.path.join(backup_dir, 'node', backup_id)], ['_ptrack']),
            "ERROR: _ptrack files was found in backup dir"
        )

    # @unittest.expectedFailure
    # @unittest.skip("skip")
    def test_fullbackup_empty_tablespace_page_after_create_table(self):
        """
        Case: Make full backup before created table in the tablespace.
                Make page backup after create table
        """

        try:
            self.backup_node(backup_dir, 'node', node, backup_type='full')
        except ProbackupException as e:
            self.assertTrue(
                False,
                "ERROR: Full backup failed.\n {0} \n {1}".format(
                    repr(self.cmd),
                    repr(e.message)
                )
            )

        node.safe_psql(
            "postgres",
            'CREATE TABLE {0} TABLESPACE {1} \
                AS SELECT i AS id, MD5(i::text) AS text, \
                MD5(repeat(i::text,10))::tsvector AS tsvector \
                FROM generate_series(0,256) i'.format('t1', tblspace_name)
        )

        backup_id = None
        try:
            backup_id = self.backup_node(backup_dir, 'node', node, backup_type='page')
        except ProbackupException as e:
            self.assertTrue(
                False,
                "ERROR: Incremental backup failed.\n {0} \n {1}".format(
                    repr(self.cmd),
                    repr(e.message)
                )
            )
        show_backup = self.show_pb(backup_dir, 'node', backup_id)
        self.assertEqual(
            "OK",
            show_backup["status"],
            "ERROR: Incremental backup status is not valid. \n Current backup status={0}".format(show_backup["status"])
        )
        self.assertTrue(
            find_by_name([self.get_tblspace_path(node, tblspace_name)], ['pg_compression']),
            "ERROR: File pg_compression not found"
        )
        self.assertTrue(
            find_by_extensions([os.path.join(backup_dir, 'node', backup_id)], ['.cmf']),
            "ERROR: .cmf files not found in backup dir"
        )
        self.assertFalse(
            find_by_extensions([os.path.join(backup_dir, 'node', backup_id)], ['_ptrack']),
            "ERROR: _ptrack files was found in backup dir"
        )

    # @unittest.expectedFailure
    # @unittest.skip("skip")
    def test_fullbackup_empty_tablespace_page_after_create_table_stream(self):
        """
        Case: Make full backup before created table in the tablespace.
                Make page backup after create table
        """

        try:
            self.backup_node(backup_dir, 'node', node, backup_type='full', options=['--stream'])
        except ProbackupException as e:
            self.assertTrue(
                False,
                "ERROR: Full backup failed.\n {0} \n {1}".format(
                    repr(self.cmd),
                    repr(e.message)
                )
            )

        node.safe_psql(
            "postgres",
            'CREATE TABLE {0} TABLESPACE {1} \
                AS SELECT i AS id, MD5(i::text) AS text, \
                MD5(repeat(i::text,10))::tsvector AS tsvector \
                FROM generate_series(0,256) i'.format('t1', tblspace_name)
        )

        backup_id = None
        try:
            backup_id = self.backup_node(backup_dir, 'node', node, backup_type='page', options=['--stream'])
        except ProbackupException as e:
            self.assertTrue(
                False,
                "ERROR: Incremental backup failed.\n {0} \n {1}".format(
                    repr(self.cmd),
                    repr(e.message)
                )
            )
        show_backup = self.show_pb(backup_dir, 'node', backup_id)
        self.assertEqual(
            "OK",
            show_backup["Status"],
            "ERROR: Incremental backup status is not valid. \n Current backup status={0}".format(show_backup["Status"])
        )
        self.assertTrue(
            find_by_name([self.get_tblspace_path(node, tblspace_name)], ['pg_compression']),
            "ERROR: File pg_compression not found"
        )
        self.assertTrue(
            find_by_extensions([os.path.join(backup_dir, 'node', backup_id)], ['.cmf']),
            "ERROR: .cmf files not found in backup dir"
        )
        self.assertFalse(
            find_by_extensions([os.path.join(backup_dir, 'node', backup_id)], ['_ptrack']),
            "ERROR: _ptrack files was found in backup dir"
        )

# --- Section: Incremental from fill tablespace --- #
    # @unittest.expectedFailure
    # @unittest.skip("skip")
    def test_fullbackup_after_create_table_ptrack_after_create_table(self):
        """
        Case:   Make full backup before created table in the tablespace.
                Make ptrack backup after create table.
                Check: incremental backup will not greater as full
        """

        node.safe_psql(
            "postgres",
            'CREATE TABLE {0} TABLESPACE {1} \
                AS SELECT i AS id, MD5(i::text) AS text, \
                MD5(repeat(i::text,10))::tsvector AS tsvector \
                FROM generate_series(0,256) i'.format('t1', tblspace_name)
        )

        backup_id_full = None
        try:
            backup_id_full = self.backup_node(backup_dir, 'node', node, backup_type='full')
        except ProbackupException as e:
            self.assertTrue(
                False,
                "ERROR: Full backup failed.\n {0} \n {1}".format(
                    repr(self.cmd),
                    repr(e.message)
                )
            )

        node.safe_psql(
            "postgres",
            'CREATE TABLE {0} TABLESPACE {1} \
                AS SELECT i AS id, MD5(i::text) AS text, \
                MD5(repeat(i::text,10))::tsvector AS tsvector \
                FROM generate_series(0,25) i'.format('t2', tblspace_name)
        )

        backup_id_ptrack = None
        try:
            backup_id_ptrack = self.backup_node(backup_dir, 'node', node, backup_type='ptrack')
        except ProbackupException as e:
            self.assertTrue(
                False,
                "ERROR: Incremental backup failed.\n {0} \n {1}".format(
                    repr(self.cmd),
                    repr(e.message)
                )
            )

        show_backup_full = self.show_pb(backup_dir, 'node', backup_id_full)[0]
        show_backup_ptrack = self.show_pb(backup_dir, 'node', backup_id_ptrack)[0]
        self.assertGreater(
            show_backup_ptrack["data-bytes"],
            show_backup_full["data-bytes"],
            "ERROR: Size of incremental backup greater as full. \n INFO: {0} >{1}".format(
                show_backup_ptrack["data-bytes"],
                show_backup_full["data-bytes"]
            )
        )

    # @unittest.expectedFailure
    # @unittest.skip("skip")
    def test_fullbackup_after_create_table_ptrack_after_create_table_stream(self):
        """
        Case:   Make full backup before created table in the tablespace (--stream).
                Make ptrack backup after create table (--stream).
                Check: incremental backup will not greater as full
        """

        node.safe_psql(
            "postgres",
            'CREATE TABLE {0} TABLESPACE {1} \
                AS SELECT i AS id, MD5(i::text) AS text, \
                MD5(repeat(i::text,10))::tsvector AS tsvector \
                FROM generate_series(0,256) i'.format('t1', tblspace_name)
        )

        backup_id_full = None
        try:
            backup_id_full = self.backup_node(backup_dir, 'node', node, backup_type='full', options=['--stream'])
        except ProbackupException as e:
            self.assertTrue(
                False,
                "ERROR: Full backup failed.\n {0} \n {1}".format(
                    repr(self.cmd),
                    repr(e.message)
                )
            )

        node.safe_psql(
            "postgres",
            'CREATE TABLE {0} TABLESPACE {1} \
                AS SELECT i AS id, MD5(i::text) AS text, \
                MD5(repeat(i::text,10))::tsvector AS tsvector \
                FROM generate_series(0,25) i'.format('t2', tblspace_name)
        )

        backup_id_ptrack = None
        try:
            backup_id_ptrack = self.backup_node(backup_dir, 'node', node, backup_type='ptrack', options=['--stream'])
        except ProbackupException as e:
            self.assertTrue(
                False,
                "ERROR: Incremental backup failed.\n {0} \n {1}".format(
                    repr(self.cmd),
                    repr(e.message)
                )
            )

        show_backup_full = self.show_pb(backup_dir, 'node', backup_id_full)
        show_backup_ptrack = self.show_pb(backup_dir, 'node', backup_id_ptrack)
        self.assertGreater(
            show_backup_ptrack["data-bytes"],
            show_backup_full["data-bytes"],
            "ERROR: Size of incremental backup greater as full. \n INFO: {0} >{1}".format(
                show_backup_ptrack["data-bytes"],
                show_backup_full["data-bytes"]
            )
        )

    # @unittest.expectedFailure
    # @unittest.skip("skip")
    def test_fullbackup_after_create_table_page_after_create_table(self):
        """
        Case:   Make full backup before created table in the tablespace.
                Make ptrack backup after create table.
                Check: incremental backup will not greater as full
        """

        node.safe_psql(
            "postgres",
            'CREATE TABLE {0} TABLESPACE {1} \
                AS SELECT i AS id, MD5(i::text) AS text, \
                MD5(repeat(i::text,10))::tsvector AS tsvector \
                FROM generate_series(0,256) i'.format('t1', tblspace_name)
        )

        backup_id_full = None
        try:
            backup_id_full = self.backup_node(backup_dir, 'node', node, backup_type='full')
        except ProbackupException as e:
            self.assertTrue(
                False,
                "ERROR: Full backup failed.\n {0} \n {1}".format(
                    repr(self.cmd),
                    repr(e.message)
                )
            )

        node.safe_psql(
            "postgres",
            'CREATE TABLE {0} TABLESPACE {1} \
                AS SELECT i AS id, MD5(i::text) AS text, \
                MD5(repeat(i::text,10))::tsvector AS tsvector \
                FROM generate_series(0,25) i'.format('t2', tblspace_name)
        )

        backup_id_page = None
        try:
            backup_id_page = self.backup_node(backup_dir, 'node', node, backup_type='page')
        except ProbackupException as e:
            self.assertTrue(
                False,
                "ERROR: Incremental backup failed.\n {0} \n {1}".format(
                    repr(self.cmd),
                    repr(e.message)
                )
            )

        show_backup_full = self.show_pb(backup_dir, 'node', backup_id_full)
        show_backup_page = self.show_pb(backup_dir, 'node', backup_id_page)
        self.assertGreater(
            show_backup_page["data-bytes"],
            show_backup_full["data-bytes"],
            "ERROR: Size of incremental backup greater as full. \n INFO: {0} >{1}".format(
                show_backup_page["data-bytes"],
                show_backup_full["data-bytes"]
            )
        )

    # @unittest.expectedFailure
    # @unittest.skip("skip")
    def test_fullbackup_after_create_table_page_after_create_table_stream(self):
        """
        Case:   Make full backup before created table in the tablespace (--stream).
                Make ptrack backup after create table (--stream).
                Check: incremental backup will not greater as full
        """

        node.safe_psql(
            "postgres",
            'CREATE TABLE {0} TABLESPACE {1} \
                AS SELECT i AS id, MD5(i::text) AS text, \
                MD5(repeat(i::text,10))::tsvector AS tsvector \
                FROM generate_series(0,256) i'.format('t1', tblspace_name)
        )

        backup_id_full = None
        try:
            backup_id_full = self.backup_node(backup_dir, 'node', node, backup_type='full', options=['--stream'])
        except ProbackupException as e:
            self.assertTrue(
                False,
                "ERROR: Full backup failed.\n {0} \n {1}".format(
                    repr(self.cmd),
                    repr(e.message)
                )
            )

        node.safe_psql(
            "postgres",
            'CREATE TABLE {0} TABLESPACE {1} \
                AS SELECT i AS id, MD5(i::text) AS text, \
                MD5(repeat(i::text,10))::tsvector AS tsvector \
                FROM generate_series(0,25) i'.format('t2', tblspace_name)
        )

        backup_id_page = None
        try:
            backup_id_page = self.backup_node(backup_dir, 'node', node, backup_type='page', options=['--stream'])
        except ProbackupException as e:
            self.assertTrue(
                False,
                "ERROR: Incremental backup failed.\n {0} \n {1}".format(
                    repr(self.cmd),
                    repr(e.message)
                )
            )

        show_backup_full = self.show_pb(backup_dir, 'node', backup_id_full)
        show_backup_page = self.show_pb(backup_dir, 'node', backup_id_page)
        self.assertGreater(
            show_backup_page["data-bytes"],
            show_backup_full["data-bytes"],
            "ERROR: Size of incremental backup greater as full. \n INFO: {0} >{1}".format(
                show_backup_page["data-bytes"],
                show_backup_full["data-bytes"]
            )
        )

# --- end ---#
    def tearDown(self):
        node.cleanup()
        self.del_test_dir(module_name, fname)
