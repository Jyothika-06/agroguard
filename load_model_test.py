from tensorflow.keras.models import load_model
import traceback
p='models/agroguard_model.keras'
try:
    m=load_model(p)
    print('Loaded model:', type(m))
except Exception as e:
    print('LOAD ERR:', type(e).__name__)
    traceback.print_exc()
