# Synthetic Data

All applicant, property, interaction, viewing, feedback and conversation records generated for this project are synthetic and created solely for demonstration.

Run:

```bash
cd backend
python scripts/generate_dataset.py
```

The generator uses a fixed seed and causal rules: stronger preference fit increases viewing probability, over-budget properties lower conversion, positive feedback increases applications, and no-response events reduce intent.

