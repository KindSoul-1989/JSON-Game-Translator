# JSON Game Translator

Open-source Windows GUI for translating game localization JSON files through an OpenAI-compatible Chat Completions API.

![Platform](https://img.shields.io/badge/platform-Windows-0078D4)
![Python](https://img.shields.io/badge/Python-3.12%2B-3776AB)
![License](https://img.shields.io/badge/license-MIT-green)

## Features

- Russian / English user interface.
- **Choose JSON → Translate → Save** workflow.
- Automatic retry (up to 4 attempts per string).
- Checkpoints and progress snapshots, so an interrupted translation can continue.
- Placeholder protection for RPG/game localization tokens such as `\\N[1]`, `\\n`, `%s`, `%1$s`, `$name`, `{player}`, and XML-like tags.
- Optional skipping of strings that already contain Cyrillic.
- Conservative filter for explicitly sexual source strings; these are left unchanged.
- No runtime Python packages are required: the GUI uses the Python standard library.
- GitHub Actions workflow builds a Windows one-file executable automatically.

## Quick start for users

Download the latest Windows executable from the repository's **Releases** page and run `JSON_Game_Translator.exe`.

The program needs an API key for the API provider you choose. The key is entered locally in the application and is not stored in the repository.

## Run from source

Requires Python 3.12+.

```bat
python json_translator_windows.py
```

No `pip install` step is needed for normal source execution.

## Build the Windows EXE locally

Run on Windows:

```bat
build_windows.bat
```

The executable is created at:

```text
dist\\JSON_Game_Translator.exe
```

The build uses PyInstaller `--onefile --windowed`. See the PyInstaller documentation for `--onefile` and platform-specific builds.

## GitHub Actions

The workflow at `.github/workflows/build-windows.yml` builds the executable on `windows-latest`.

- Push to `main`: runs a build check.
- Push a tag such as `v1.0.0`: builds the EXE and publishes a GitHub Release containing the executable.
- Manual **Run workflow** is also available from the Actions tab.

## Project structure

```text
JSON-Game-Translator/
├── .github/
│   ├── workflows/
│   │   └── build-windows.yml
│   └── ISSUE_TEMPLATE/
├── json_translator_windows.py
├── build_windows.bat
├── requirements-build.txt
├── tests/
├── CHANGELOG.md
├── CONTRIBUTING.md
├── SECURITY.md
├── LICENSE
├── VERSION
├── pyproject.toml
├── .gitignore
└── README.md
```

## Progress files

For a source file such as `game.json`, the translator may create:

- `game.json.ru.checkpoint.json` — completed translation entries used for resume.
- `game.json.ru-progress.json` — latest autosaved JSON snapshot.

These files are intentionally ignored by Git.

## API compatibility

The application sends requests to:

```text
{API URL}/chat/completions
```

with the standard `model`, `messages`, and `temperature` fields. It therefore works with providers exposing an OpenAI-compatible Chat Completions endpoint.

## Security notes

- Never commit an API key.
- Do not put an API key into screenshots or GitHub issues.
- The application does not upload your JSON anywhere except the API endpoint you configure.
- Review your provider's data-retention and privacy policy before translating proprietary game text.

## License

MIT. See [LICENSE](LICENSE).
