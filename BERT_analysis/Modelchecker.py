import os

# Disable TF/Flax to avoid pulling in tensorflow and problematic protobuf
os.environ["TRANSFORMERS_NO_TF"] = "1"
os.environ["TRANSFORMERS_NO_FLAX"] = "1"

from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline

# Use the *subfolder* that actually contains config.json, tokenizer.json, etc.
MODEL_PATH = "BERT_model/my-finetuned-ner-400-2nd-model"

tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
model = AutoModelForTokenClassification.from_pretrained(MODEL_PATH)

ner_pipeline = pipeline(
    "ner",
    model=model,
    tokenizer=tokenizer,
    aggregation_strategy="simple",
    device=-1,  # CPU; change to 0 if you have a CUDA GPU and proper setup
)

print("Model loaded successfully!")
