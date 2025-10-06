import pandas as pd
import ollama
from deepeval.models.base_model import DeepEvalBaseLLM
from deepeval import evaluate
from deepeval.test_case import LLMTestCase
from deepeval.metrics import AnswerRelevancyMetric, FaithfulnessMetric, ContextualPrecisionMetric, ContextualRecallMetric


class OllamaLlama3(DeepEvalBaseLLM):
    def __init__(self, model_name: str = "llama3.2"):
        self.model_name = model_name
        

    def load_model(self):
        return self.model_name

    def generate(self, prompt: str) -> str:
        response = ollama.generate(
            model=self.model_name,
            prompt=prompt,
            options={'num_predict': 100, 'temperature':0}
        )
        return response['response']

    async def a_generate(self, prompt: str) -> str:
        return self.generate(prompt)

    def get_model_name(self):
        return f"Ollama {self.model_name}"



llama3 = OllamaLlama3(model_name= "llama3.2")
df = pd.read_excel("results.xlsx")

test_cases = []
for _, row in df.iterrows():
    test_case = LLMTestCase(
        input=row["user_input"],
        actual_output=row["response"],
        expected_output=row["reference"],
        retrieval_context=[row["retrieved_contexts"]] if pd.notna(row["retrieved_contexts"]) else []
    )
    test_cases.append(test_case)
answer_relevancy_metric = AnswerRelevancyMetric(model=llama3, threshold=0.7)
evaluate(test_cases=test_cases, metrics=[answer_relevancy_metric])