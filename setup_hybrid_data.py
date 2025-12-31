"""
Setup script to populate both ChromaDB and Neo4j with sample data
Run this script once before using the hybrid RAG system
"""

import os
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

# Configuration
API_KEY = os.getenv("GOOGLE_API_KEY")
CHROMA_PERSIST_DIR = "./chroma_db"
CHROMA_COLLECTION_NAME = os.getenv("CHROMA_COLLECTION")
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE")


def setup_neo4j():
    """Setup Neo4j with users, companies, and relationships"""
    print("Setting up Neo4j database...")
    
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    with driver.session(database=NEO4J_DATABASE) as session:
        # Clear existing data (optional - comment out if you want to keep existing data)
        print("  - Clearing existing data...")
        session.run("MATCH (n) DETACH DELETE n")
        
        # Create Users
        print("  - Creating users...")
        session.run("""
            CREATE 
              (u1:User {id: 1, name: 'Alice Johnson', email: 'alice@example.com'}),
              (u2:User:Director {id: 2, name: 'Bob Smith', email: 'bob@example.com'}),
              (u3:User {id: 3, name: 'Charlie Brown', email: 'charlie@example.com'}),
              (u4:User {id: 4, name: 'Diana Prince', email: 'diana@example.com'}),
              (u5:User {id: 5, name: 'Ethan Hunt', email: 'ethan@example.com'}),
              (u6:User:Director {id: 6, name: 'Fiona Green', email: 'fiona@example.com'}),
              (u7:User {id: 7, name: 'George Martin', email: 'george@example.com'}),
              (u8:User {id: 8, name: 'Hannah Lee', email: 'hannah@example.com'}),
              (u9:User {id: 9, name: 'Ian Wright', email: 'ian@example.com'}),
              (u10:User {id: 10, name: 'Julia Roberts', email: 'julia@example.com'})
        """)
        
        # Create Companies
        print("  - Creating companies...")
        session.run("""
            CREATE 
              (c1:Company {
                id: 1, 
                name: 'TechCorp Solutions', 
                industry: 'Technology',
                founded: 2015,
                employees: 250
              }),
              (c2:Company {
                id: 2, 
                name: 'Global Innovations Ltd', 
                industry: 'Manufacturing',
                founded: 2010,
                employees: 500
              })
        """)
        
        # Create FRIEND relationships
        print("  - Creating friend relationships...")
        session.run("""
            MATCH (u1:User {id: 1}), (u3:User {id: 3}), (u5:User {id: 5}),
                  (u2:User {id: 2}), (u4:User {id: 4}), (u7:User {id: 7}),
                  (u6:User {id: 6}), (u8:User {id: 8}), (u9:User {id: 9}), (u10:User {id: 10})
            CREATE 
              (u1)-[:FRIEND {since: 2020}]->(u3),
              (u1)-[:FRIEND {since: 2021}]->(u5),
              (u2)-[:FRIEND {since: 2019}]->(u1),
              (u2)-[:FRIEND {since: 2022}]->(u3),
              (u3)-[:FRIEND {since: 2018}]->(u8),
              (u4)-[:FRIEND {since: 2021}]->(u6),
              (u5)-[:FRIEND {since: 2020}]->(u9),
              (u6)-[:FRIEND {since: 2019}]->(u10),
              (u7)-[:FRIEND {since: 2023}]->(u1),
              (u8)-[:FRIEND {since: 2022}]->(u2)
        """)
        
        # Create WORKS_AT relationships
        print("  - Creating employment relationships...")
        session.run("""
            MATCH (u2:User {id: 2}), (c1:Company {id: 1})
            CREATE (u2)-[:WORKS_AT {role: 'Senior Data Engineer', since: 2018}]->(c1)
        """)
        
        session.run("""
            MATCH (u1:User {id: 1}), (c1:Company {id: 1})
            CREATE (u1)-[:WORKS_AT {role: 'ML Engineer', since: 2019}]->(c1)
        """)
        
        session.run("""
            MATCH (u3:User {id: 3}), (c2:Company {id: 2})
            CREATE (u3)-[:WORKS_AT {role: 'Product Manager', since: 2020}]->(c2)
        """)
        
        # Create DIRECTS relationships
        print("  - Creating director relationships...")
        session.run("""
            MATCH (u2:User {id: 2}), (c2:Company {id: 2})
            CREATE (u2)-[:DIRECTS {since: 2022}]->(c2)
        """)
        
        session.run("""
            MATCH (u6:User {id: 6}), (c1:Company {id: 1})
            CREATE (u6)-[:DIRECTS {since: 2021}]->(c1)
        """)
    
    driver.close()
    print("✓ Neo4j setup complete!\n")


def setup_chromadb():
    """Setup ChromaDB with user and company documents"""
    print("Setting up ChromaDB...")
    
    # Initialize embeddings
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        api_key=API_KEY
    )
    
    # Create or load vector store
    if os.path.exists(CHROMA_PERSIST_DIR):
        print(f"  - Loading existing ChromaDB from {CHROMA_PERSIST_DIR}...")
        vector_store = Chroma(
            collection_name=CHROMA_COLLECTION_NAME,
            persist_directory=CHROMA_PERSIST_DIR,
            embedding_function=embeddings
        )
        # Clear existing data
        print("  - Clearing existing ChromaDB data...")
        try:
            vector_store.delete_collection()
        except:
            pass
    
    print(f"  - Creating new ChromaDB in {CHROMA_PERSIST_DIR}...")
    vector_store = Chroma(
        collection_name=CHROMA_COLLECTION_NAME,
        persist_directory=CHROMA_PERSIST_DIR,
        embedding_function=embeddings
    )
    
    # Create documents for users
    user_documents = [
        Document(
            page_content="Alice Johnson is a machine learning engineer with expertise in deep learning and neural networks. She has published research papers on computer vision and natural language processing. Alice holds a PhD in Computer Science from MIT and specializes in building production ML systems. She has experience with TensorFlow, PyTorch, and cloud ML platforms.",
            metadata={"type": "user_bio", "user_id": 1, "name": "Alice Johnson"}
        ),
        Document(
            page_content="Bob Smith is a seasoned data engineer with over 10 years of experience in building scalable data pipelines and ETL systems. He specializes in Python, Apache Spark, and cloud data platforms. Bob is passionate about data architecture and mentoring junior engineers. He has expertise in real-time streaming, data lakes, and dimensional modeling.",
            metadata={"type": "user_bio", "user_id": 2, "name": "Bob Smith"}
        ),
        Document(
            page_content="Bob Smith's technical skills include: Python, SQL, Apache Spark, Apache Airflow, Apache Kafka, AWS (S3, Redshift, EMR, Glue), Docker, Kubernetes, Terraform. He has certifications in AWS Solutions Architect Professional and Google Cloud Professional Data Engineer. Bob is proficient in data modeling, pipeline optimization, and cost reduction strategies.",
            metadata={"type": "user_skills", "user_id": 2, "name": "Bob Smith"}
        ),
        Document(
            page_content="Bob Smith's notable projects: 1) Led migration of legacy data warehouse to cloud-based data lake architecture, resulting in 40% cost reduction and 3x query performance improvement. 2) Designed and implemented real-time streaming pipelines processing 10M events per day using Kafka and Spark Streaming. 3) Architected a centralized machine learning feature store serving 15+ data science models. 4) Built automated data quality monitoring system reducing data incidents by 60%.",
            metadata={"type": "user_projects", "user_id": 2, "name": "Bob Smith"}
        ),
        Document(
            page_content="Charlie Brown is a product manager focused on B2B SaaS products. He has 7 years of experience in agile methodologies and user-centered design. Charlie previously worked in consulting at McKinsey before transitioning to product management. He specializes in product strategy, roadmap planning, and stakeholder management. Charlie has launched 5 successful products with combined ARR of $20M.",
            metadata={"type": "user_bio", "user_id": 3, "name": "Charlie Brown"}
        ),
        Document(
            page_content="Diana Prince is a UX designer with a background in psychology. She has worked on mobile app design for fintech companies and has expertise in user research, prototyping, and design systems. Diana is passionate about accessibility and inclusive design.",
            metadata={"type": "user_bio", "user_id": 4, "name": "Diana Prince"}
        ),
        Document(
            page_content="Fiona Green is an experienced technology executive with 15 years in software development and team leadership. She has served as CTO for two startups and currently holds director positions at multiple tech companies. Fiona specializes in scaling engineering teams and building technical strategy.",
            metadata={"type": "user_bio", "user_id": 6, "name": "Fiona Green"}
        ),
    ]
    
    # Create documents for companies
    company_documents = [
        Document(
            page_content="TechCorp Solutions is a leading technology company specializing in cloud-based data analytics and AI solutions. Founded in 2015, the company has grown to 250 employees and serves Fortune 500 clients. TechCorp is known for its innovative approach to real-time data processing and predictive analytics. The company has raised $50M in Series B funding and is expanding internationally.",
            metadata={"type": "company_info", "company_id": 1, "name": "TechCorp Solutions"}
        ),
        Document(
            page_content="TechCorp Solutions offers several product lines: 1) DataFlow - a real-time data pipeline platform, 2) AI Studio - a machine learning operations platform, 3) Analytics Hub - a business intelligence solution. The company focuses on industries like finance, healthcare, and retail. TechCorp's technology stack is built on AWS and uses modern data engineering tools.",
            metadata={"type": "company_products", "company_id": 1, "name": "TechCorp Solutions"}
        ),
        Document(
            page_content="Global Innovations Ltd is a manufacturing company that produces advanced industrial equipment and automation solutions. Established in 2010, the company focuses on sustainable manufacturing practices and Industry 4.0 technologies. They operate facilities in North America, Europe, and Asia with 500 employees worldwide. Global Innovations is a leader in smart factory solutions and robotics.",
            metadata={"type": "company_info", "company_id": 2, "name": "Global Innovations Ltd"}
        ),
    ]
    
    # Combine all documents
    all_documents = user_documents + company_documents
    
    print(f"  - Adding {len(all_documents)} documents to ChromaDB...")
    vector_store.add_documents(all_documents)
    
    print("✓ ChromaDB setup complete!\n")


def verify_setup():
    """Verify that both databases are set up correctly"""
    print("Verifying setup...")
    
    # Verify Neo4j
    print("\n1. Neo4j Verification:")
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    with driver.session(database=NEO4J_DATABASE) as session:
        user_count = session.run("MATCH (u:User) RETURN count(u) as count").single()["count"]
        company_count = session.run("MATCH (c:Company) RETURN count(c) as count").single()["count"]
        rel_count = session.run("MATCH ()-[r]->() RETURN count(r) as count").single()["count"]
        
        print(f"   - Users: {user_count}")
        print(f"   - Companies: {company_count}")
        print(f"   - Relationships: {rel_count}")
    driver.close()
    
    # Verify ChromaDB
    print("\n2. ChromaDB Verification:")
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        api_key=API_KEY
    )
    vector_store = Chroma(
        collection_name=CHROMA_COLLECTION_NAME,
        persist_directory=CHROMA_PERSIST_DIR,
        embedding_function=embeddings
    )
    
    collection = vector_store._collection
    doc_count = collection.count()
    print(f"   - Documents: {doc_count}")
    
    print("\n✓ Setup verification complete!")
    print("\nYou can now run the hybrid RAG system!")


if __name__ == "__main__":
    print("="*70)
    print("HYBRID RAG SETUP - ChromaDB + Neo4j")
    print("="*70)
    print()
    
    try:
        setup_neo4j()
        setup_chromadb()
        verify_setup()
        
        print("\n" + "="*70)
        print("SUCCESS! Both databases are ready.")
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ Error during setup: {e}")
        import traceback
        traceback.print_exc()