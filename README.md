# Fine tuning deepseek-r1 to map terms to ontologies.

## Strategy

1. Create training data by using the EFO ontology and the EFO synonyms.
2. Use the training data to fine tune the deepseek-r1 model.
3. Use the fine tuned model to map terms to the EFO ontology.

## Training data

For the EFO terms get the list of synonyms from the EFO ontology and use them as the training data. Also use the EFO ontology to get the hierarchy of the terms and use it as the training data. Enhance the training data by adding the synonyms of the parent terms to the training data. Create more synonyms by using the wordnet synonyms. Also add random strings in brackets as new synonyms so that the model can learn to ignore them.


## Fine tuning

Suggest using the QLoRa model for finetuning to make it faster (https://pytorch.org/blog/finetune-llms/).


## Mapping

Could use prompts but no guarantee that results will be true EFO terms. Alternatively pre-calculate the embeddings for all EFO terms after training and use the embeddings to find the closest term to the input term. This will be faster but may not be as accurate as using prompts.

## Model

Consider using deepseek-r1 model

```
git lfs install
git clone https://huggingface.co/deepseek-ai/deepseek-coder-1.3b-base
```


## Need CUDA installed e.g.

```python
import torch

def check_cuda():
    if torch.cuda.is_available():
        print("CUDA is available.")
        print(f"CUDA version: {torch.version.cuda}")
        print(f"Number of GPUs: {torch.cuda.device_count()}")
        print(f"Current GPU: {torch.cuda.current_device()}")
        print(f"GPU Name: {torch.cuda.get_device_name(torch.cuda.current_device())}")
    else:
        print("CUDA is not available.")

check_cuda()
```

## Notes

- Output the confidence of the mapping
- Set temperature parameter to low during mapping
- Validate output - needs to be a true EFO
- Try just providing a query that includes a csv of existing trait - EFO mappings

