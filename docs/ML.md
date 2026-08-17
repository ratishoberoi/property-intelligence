# ML

The project includes prototype models trained only on synthetic data.

## Property Matching

Matching uses hard filters followed by transparent feature scoring:

- budget match
- bedroom match
- location match
- property type match
- amenity match
- furnished match
- parking match
- pet match
- behavioural similarity
- historical preference match

## Intent

Intent classes are `VERY_HIGH`, `HIGH`, `MEDIUM`, `LOW`, `DORMANT`. If a trained model exists, the backend loads it. If not, deterministic rules are used.

## Conversion

Conversion scoring estimates synthetic probability of progressing to application activity. It exposes positive and negative factors and does not claim real-world accuracy.

