# Donizo Truth Engine - Quick Start Guide

## 🚀 One-Command Start

No installation required! Just Docker.

### Linux / macOS:

```bash
./start.sh
```

### Windows:

```cmd
start.bat
```

### Alternative (Docker Compose):

```bash
docker-compose run --rm donizo-engine
```

---

## 📋 What You Get

After running the command, you'll see an **interactive menu** with these options:

```
====================================================================
     DONIZO TRUTH ENGINE - Interactive Menu
     Version 0.1.0
====================================================================

📋 MAIN MENU:
------------------------------------------------------------
  [1] 🧪 Run All Tests
  [2] 📊 Generate Test Data (1000+ events)
  [3] ▶️  Run Engine (Process Events)
  [4] 🔄 Replay Mode (Verify Determinism)
  [5] 📁 View Generated Files
  [6] 📈 Show Statistics
  [7] 🧹 Clean Generated Files
  [8] ℹ️  Help & Documentation
  [9] 🐚 Open Shell (Advanced)
  [0] 🚪 Exit
------------------------------------------------------------
```

---

## 🎯 Recommended Workflow

### First Time:

1. **Run Tests** (Option 1)
   - Verifies everything works correctly
   - Runs comprehensive test suite

2. **Generate Test Data** (Option 2)
   - Creates 1000+ synthetic events
   - Demonstrates all pricing scenarios

3. **Run Engine** (Option 3)
   - Processes the events
   - Learns pricing biases
   - Generates audit log

4. **Replay Mode** (Option 4)
   - Verifies determinism
   - Confirms identical results

5. **View Statistics** (Option 6)
   - Analyze decisions made
   - Review pricing patterns

---

## 📁 Data Persistence

All generated files are stored in the `./data` directory on your host machine:

- `data/events.jsonl` - Input events
- `data/rules_state.json` - Learned pricing rules
- `data/audit_log.jsonl` - Decision audit trail

These files persist between Docker runs.

---

## 🛠 Requirements

### For Docker Setup (Recommended)

**Only Docker is required!**

- Docker Desktop (Windows/Mac)
- Docker Engine (Linux)

No Python, no libraries, no dependencies on your machine.

### For Local Development Setup

If you prefer running locally without Docker:

- Python 3.10 or higher
- Virtual environment (venv) - **Python best practice**

**Quick local setup:**
```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # Linux/macOS
# OR
venv\Scripts\activate     # Windows

# Install
pip install -r requirements.txt
pip install -e .
```

See `README.md` for detailed local installation instructions.

---

## 💡 Tips

### Clean Start

If you want to start fresh:
- Choose Option 7 (Clean Generated Files)
- Or delete the `./data` directory

### Advanced Usage

- Option 9 opens a shell inside the container
- Useful for manual commands or debugging

### View Files

Option 5 lets you inspect generated files:
- View sample events
- Check audit logs
- Review learned state

---

## 🐛 Troubleshooting

### Docker Build Fails

Make sure Docker is running:
```bash
docker --version
```

### Permission Denied (Linux/Mac)

Make script executable:
```bash
chmod +x start.sh
./start.sh
```

### Port Already in Use

Stop existing containers:
```bash
docker ps
docker stop donizo-truth-engine
```

---

## 📖 Next Steps

After exploring the interactive menu:

1. Read `README.md` for detailed documentation
2. Review `donizo_truth_engine_prd.md` for system requirements
3. Check `PROJECT_BREAKDOWN.md` for architecture details

---

## 🎓 What This Demonstrates

This project showcases:

✅ **Deterministic Financial Systems**
- Integer-only math (no floating-point errors)
- Reproducible results (cryptographic verification)
- Full audit trail

✅ **Production-Ready Code**
- Comprehensive test coverage
- Type safety with Pydantic
- Error handling and validation

✅ **Clean Architecture**
- Separation of concerns
- Event sourcing pattern
- State management

✅ **Developer Experience**
- Zero-install via Docker
- Interactive menu system
- Clear documentation

---

## 📞 Support

For issues or questions:
1. Check the Help menu (Option 8)
2. Review README.md
3. Open an issue on GitHub

---

**Enjoy exploring the Donizo Truth Engine!** 🎉
