import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, TrainingArguments, Trainer
from datasets import Dataset
import pandas as pd
from typing import List, Dict, Tuple
from dataclasses import dataclass
from peft import (
    LoraConfig,
    prepare_model_for_kbit_training,
    get_peft_model,
)
from transformers import BitsAndBytesConfig

@dataclass
class DataCollator:
    tokenizer: AutoTokenizer
    max_length: int = 512
    
    def __call__(self, features: List[Dict[str, str]]) -> Dict[str, torch.Tensor]:
        formatted_texts = [
            f"Map the following phenotype to its EFO term:\nPhenotype: {item['phenotype']}\nEFO Term: {item['efo_term']}"
            for item in features
        ]
        
        batch = self.tokenizer(
            formatted_texts,
            padding=True,
            truncation=True,
            max_length=self.max_length,
            return_tensors="pt"
        )
        
        batch["labels"] = batch["input_ids"].clone()
        return batch

class PhenotypeMapper:
    def __init__(self, model_path: str, device: str = "cuda"):
        self.tokenizer = AutoTokenizer.from_pretrained(
            model_path,
            trust_remote_code=True,
            local_files_only=True,
            padding_side="right"
        )
        
        # Configure 4-bit quantization
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True,
        )
        
        # Load model with quantization
        self.model = AutoModelForCausalLM.from_pretrained(
            model_path,
            trust_remote_code=True,
            local_files_only=True,
            quantization_config=bnb_config,
            device_map="auto"
        )
        
        # Prepare model for k-bit training
        self.model = prepare_model_for_kbit_training(self.model)
        
        # Configure LoRA
        lora_config = LoraConfig(
            r=16,  # rank
            lora_alpha=32,
            target_modules=["q_proj", "v_proj"],  # Adjust based on model architecture
            lora_dropout=0.05,
            bias="none",
            task_type="CAUSAL_LM"
        )
        
        # Get PEFT model
        self.model = get_peft_model(self.model, lora_config)
        
        # Print trainable parameters info
        self.model.print_trainable_parameters()
        
    def prepare_training_data(self, phenotype_efo_pairs: List[Tuple[str, str]]) -> Dataset:
        """
        Convert phenotype-EFO pairs into a format suitable for training.
        """
        training_data = [
            {
                "phenotype": phenotype,
                "efo_term": efo_term
            }
            for phenotype, efo_term in phenotype_efo_pairs
        ]
        
        return Dataset.from_pandas(pd.DataFrame(training_data))
    
    def train(self, 
              training_data: Dataset,
              output_dir: str = "phenotype_mapper_model",
              num_epochs: int = 3,
              batch_size: int = 8,
              learning_rate: float = 2e-4):  # Slightly higher LR for LoRA
        """
        Fine-tune the model using QLoRA.
        """
        training_args = TrainingArguments(
            output_dir=output_dir,
            num_train_epochs=num_epochs,
            per_device_train_batch_size=batch_size,
            learning_rate=learning_rate,
            weight_decay=0.01,
            save_strategy="epoch",
            logging_dir="./logs",
            remove_unused_columns=False,
            fp16=True,  # Mixed precision training
            gradient_accumulation_steps=4,
            warmup_ratio=0.05,
        )
        
        data_collator = DataCollator(self.tokenizer)
        
        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=training_data,
            data_collator=data_collator,
            tokenizer=self.tokenizer
        )
        
        trainer.train()
        
        # Save adapter weights only
        self.model.save_pretrained(output_dir)
    
    def load_adapter(self, adapter_path: str):
        """
        Load trained adapter weights.
        """
        self.model.load_adapter(adapter_path)

# Example usage
if __name__ == "__main__":
training_pairs = [
    ("Type 2 diabetes", "type 2 diabetes mellitus"),
    ("High blood pressure", "hypertensive disorder"),
    # Add more pairs...
]
    
MODEL_PATH = "/home/gh13047/downloads/deepseek-coder-1.3b-base"
mapper = PhenotypeMapper(model_path=MODEL_PATH)
    
# Train
training_dataset = mapper.prepare_training_data(training_pairs)
mapper.train(training_dataset)
