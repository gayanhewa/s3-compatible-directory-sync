"""Tests for menu bar app."""

from unittest.mock import MagicMock, patch

import pytest


def _make_app(tmp_watch_dir):
    """Create a SyncMenuBarApp with rumps internals bypassed."""
    from s3_folder_sync.menubar import SyncMenuBarApp

    with patch.object(SyncMenuBarApp, "__init__", lambda self, path: None):
        app = SyncMenuBarApp.__new__(SyncMenuBarApp)
        app.watch_path = tmp_watch_dir
        app.config = None
        app.engine = None
        app.db = None
        app._syncing = False
        app._running = False
        app._sync_thread = None
        app._last_sync = "never"
        app._conflict_count = 0
        app._file_count = 0
        app.title = "⇅"
        # Use a plain dict to avoid rumps _menu descriptor
        app._mock_menu = {
            "Status: Idle": MagicMock(title="Status: Idle"),
            "Last sync: never": MagicMock(title="Last sync: never"),
            "Files: 0 tracked": MagicMock(title="Files: 0 tracked"),
            "Conflicts: none": MagicMock(title="Conflicts: none"),
            "Start Sync": MagicMock(title="Start Sync"),
        }
        # Monkey-patch menu access to use our dict
        type(app).menu = property(
            lambda self: self._mock_menu,
            lambda self, v: setattr(self, "_mock_menu", v),
        )
        return app


class TestSyncMenuBarApp:
    def test_init_without_config(self, tmp_watch_dir):
        app = _make_app(tmp_watch_dir)
        app._load_config()
        assert app.config is None

    def test_init_with_config(self, config, mock_s3, tmp_watch_dir):
        config.save()
        app = _make_app(tmp_watch_dir)
        app._load_config()
        assert app.config is not None
        assert app.engine is not None
        assert app.db is not None

    def test_do_sync(self, config, mock_s3, tmp_watch_dir):
        config.save()
        (tmp_watch_dir / "test.md").write_text("hello")

        app = _make_app(tmp_watch_dir)
        app._load_config()
        app._do_sync()

        assert app._last_sync != "never"
        assert app._file_count == 1

    def test_do_sync_updates_status(self, config, mock_s3, tmp_watch_dir):
        config.save()
        (tmp_watch_dir / "a.md").write_text("aaa")
        (tmp_watch_dir / "b.md").write_text("bbb")

        app = _make_app(tmp_watch_dir)
        app._load_config()
        app._do_sync()

        assert app._file_count == 2
        assert app._conflict_count == 0

    def test_do_sync_skips_when_already_syncing(self, config, mock_s3, tmp_watch_dir):
        config.save()
        app = _make_app(tmp_watch_dir)
        app._load_config()
        app._syncing = True

        # Should return immediately without changing state
        old_last_sync = app._last_sync
        app._do_sync()
        assert app._last_sync == old_last_sync

    def test_open_folder(self, tmp_watch_dir):
        app = _make_app(tmp_watch_dir)
        with patch("subprocess.Popen") as mock_popen:
            app._on_open_folder(None)
            mock_popen.assert_called_once_with(["open", str(tmp_watch_dir)])

    def test_view_conflicts_empty(self, tmp_watch_dir):
        app = _make_app(tmp_watch_dir)
        with patch("s3_folder_sync.menubar.rumps") as mock_rumps:
            app._on_view_conflicts(None)
            mock_rumps.notification.assert_called_once()

    def test_view_conflicts_found(self, tmp_watch_dir):
        (tmp_watch_dir / "doc.conflict.mac1.20240101.md").write_text("conflict")
        app = _make_app(tmp_watch_dir)
        with patch("s3_folder_sync.menubar.rumps") as mock_rumps:
            app._on_view_conflicts(None)
            mock_rumps.alert.assert_called_once()

    def test_start_stop_toggle(self, config, mock_s3, tmp_watch_dir):
        config.save()
        app = _make_app(tmp_watch_dir)
        app._load_config()

        # Start
        with patch.object(app, "_start_sync_loop"):
            app._on_start_stop(MagicMock())
            assert app._running is True

        # Stop
        app._on_start_stop(MagicMock())
        assert app._running is False

    def test_sync_now_without_config(self, tmp_watch_dir):
        app = _make_app(tmp_watch_dir)
        with patch("s3_folder_sync.menubar.rumps") as mock_rumps:
            app._on_sync_now(MagicMock())
            mock_rumps.notification.assert_called_once()

    def test_update_status(self, tmp_watch_dir):
        app = _make_app(tmp_watch_dir)
        app._update_status("Syncing...")
        assert app.menu["Status: Idle"].title == "Status: Syncing..."

    def test_update_menu_with_conflicts(self, tmp_watch_dir):
        app = _make_app(tmp_watch_dir)
        app._conflict_count = 3
        app._file_count = 10
        app._last_sync = "12:00:00"
        app._running = True
        app._update_menu()

        assert app.menu["Conflicts: none"].title == "Conflicts: 3"
        assert app.menu["Files: 0 tracked"].title == "Files: 10 tracked"
        assert app.menu["Last sync: never"].title == "Last sync: 12:00:00"


class TestMenuBarCLI:
    def test_menubar_command_missing_rumps(self, tmp_watch_dir):
        from click.testing import CliRunner
        from s3_folder_sync.cli import main

        with patch.dict("sys.modules", {"rumps": None}):
            import importlib
            import s3_folder_sync.menubar
            with patch("s3_folder_sync.cli.sys.exit") as mock_exit:
                mock_exit.side_effect = SystemExit(1)
                runner = CliRunner()
                result = runner.invoke(main, ["menubar", "--path", str(tmp_watch_dir)])
                assert result.exit_code != 0
