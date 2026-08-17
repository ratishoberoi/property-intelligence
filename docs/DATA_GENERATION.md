# Data Generation

All data is synthetic and deterministic. The generator uses seed `42`.

Generated volumes:

- At least 2,000 properties
- At least 1,000 applicants
- At least 15,000 interactions
- At least 3,000 viewings
- At least 2,000 feedback records
- At least 5,000 conversations

The generator is not purely random. Applicant-property affinity influences property views, viewing bookings, feedback sentiment and application probability. Over-budget properties increase price objections. Positive feedback increases conversion probability. No-response and cancelled viewings reduce downstream intent labels.

