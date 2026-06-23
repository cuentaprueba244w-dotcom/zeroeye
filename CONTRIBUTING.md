# Contributing to zeroeye

## Dev Setup
- Python 3.10+  |  Rust  |  Node.js 18+

```bash
git clone ...
cd zeroeye
cd backend && cargo build
cd ../frontend && npm install
```

## Build
```
python3 build.py
```

## PR Process
1. Branch from main
2. Make changes, run build.py
3. Include diagnostic/ artifacts
4. Submit PR

## Style
- Python: Black + type hints  |  Rust: rustfmt  |  TS/JS: Prettier