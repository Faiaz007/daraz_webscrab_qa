import os
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from transformers import pipeline
import torch

class LaptopQASystem:
    def __init__(self, csv_path="laptops.csv"):
        csv_path = self.find_data_file(csv_path)
        self.df = pd.read_csv(csv_path)
        self.clean_data()
        self.initialize_models()
        self.generate_embeddings()
    
    def find_data_file(self, data_path):
        """Search for the CSV data file"""
        if os.path.exists(data_path):
            return data_path
        possible_paths = [
            "./scraper/data/laptops.csv",  
            "laptops.csv",                
            "f:/daraz_webscrab_qa/scraper/data/laptops.csv"  
        ]
        for path in possible_paths:
            if os.path.exists(path):
                print(f"Found data at: {path}")
                return path
        raise FileNotFoundError("CSV file not found.")

    def clean_data(self):
        """Clean the CSV data"""
        self.df.columns = self.df.columns.str.strip().str.lower()
        # Handle price as numeric and remove non-numeric symbols
        self.df['price'] = pd.to_numeric(
            self.df['price'].astype(str).str.replace(',', '').str.extract('(\d+)')[0],
            errors='coerce'
        )
        self.df.dropna(subset=['price'], inplace=True)  # Remove rows with invalid price
        # Create a text column for embedding
        self.df['text'] = self.df.apply(lambda row: f"Title: {row['title']}\nPrice: {row['price']}", axis=1)
    
    def initialize_models(self):
        """Initialize embedding model and LLM"""
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.llm = pipeline(
            "text-generation",
            model="distilgpt2",  
            device="cuda" if torch.cuda.is_available() else "cpu"
        )
    
    def generate_embeddings(self):
        """Generate embeddings for all laptop descriptions"""
        print("Generating embeddings...")
        self.df['embedding'] = self.df['text'].apply(
            lambda x: self.embedding_model.encode(x)
        )
        print("Embeddings generated successfully.")
    
    def retrieve_relevant_docs(self, query, top_k=3):
        """Retrieve the most relevant documents using cosine similarity"""
        query_embedding = self.embedding_model.encode(query)
        similarities = self.df['embedding'].apply(
            lambda x: cosine_similarity([query_embedding], [x])[0][0]
        )
        top_indices = similarities.argsort()[-top_k:][::-1]
        return self.df.iloc[top_indices]
    
    def generate_answer(self, question):
        """Generate an answer using RAG approach"""
        try:
            # Retrieve relevant documents
            relevant_docs = self.retrieve_relevant_docs(question)
            context = "\n\n".join(relevant_docs['text'].tolist())
            
            # Create a prompt for the LLM
            prompt = f"""You are a helpful laptop shopping assistant. Answer the question based only on the following product information.
            Be specific about models, prices, and features when relevant. If you don't know the answer, say you don't know.
            
            Available Products:
            {context}
            
            Question: {question}
            Answer:"""
            
            # Generate answer
            answer = self.llm(
                prompt,
                max_new_tokens=150,
                do_sample=True,
                temperature=0.5,
                top_p=0.9
            )[0]['generated_text']
            
            return answer.split("Answer:")[-1].strip()
        
        except Exception as e:
            return f"Sorry, I encountered an error: {str(e)}"
    
    def chat_interface(self):
        """Command-line interface for chatting with the Q&A system"""
        print("Laptop Q&A System. Type 'quit' or 'exit' to end the session.")
        print("You can ask about laptop prices, models, or comparisons.")
        
        while True:
            question = input("\nQuestion: ")
            if question.lower() in ['quit', 'exit']:
                print("Goodbye!")
                break
            
            print("\nThinking...")
            answer = self.generate_answer(question)
            print(f"\nAnswer: {answer}\n")
            
            # Show sources for transparency
            relevant_docs = self.retrieve_relevant_docs(question)
            print("Relevant products considered:")
            for _, row in relevant_docs.iterrows():
                print(f"- {row['title']} (Price: {row['price']})")


if __name__ == "__main__":
    try:
        qa = LaptopQASystem()
        qa.chat_interface()
    except Exception as e:
        print(f"Failed to initialize the Q&A system: {str(e)}")
