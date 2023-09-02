import firebase_admin
from firebase_admin import credentials, firestore

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)

db = firestore.client()

collection_ref = db.collection("靜宜資管")
docs = collection_ref.where("lab","==", 579).get()
for doc in docs:
    doc_ref = db.collection("靜宜資管").document(doc.id)
    doc_ref.delete()
