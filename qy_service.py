from flask import Flask, request, jsonify
import cv2
import numpy as np
from pyzbar import pyzbar
import base64
import json
import logging
from datetime import datetime
import os

# Logging ayarları
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/qr_service.log'),
        logging.StreamHandler()
    ]
)

app = Flask(__name__)

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "qr-reader"
    }), 200

@app.route('/read-qr', methods=['POST'])
def read_qr():
    """QR kod okuma endpoint'i"""
    try:
        app.logger.info("QR okuma isteği alındı")
        
        # Request validation
        if not request.json or 'image' not in request.json:
            return jsonify({
                "success": False,
                "error": "Base64 image verisi gerekli"
            }), 400
        
        # Base64 image al
        image_data = request.json['image']
        
        # Base64'ü decode et
        try:
            # Data URL prefix'ini temizle (data:image/jpeg;base64, gibi)
            if ',' in image_data:
                image_data = image_data.split(',')[1]
            
            image_bytes = base64.b64decode(image_data)
        except Exception as e:
            app.logger.error(f"Base64 decode hatası: {str(e)}")
            return jsonify({
                "success": False,
                "error": "Base64 decode hatası"
            }), 400
        
        # NumPy array'e çevir
        nparr = np.frombuffer(image_bytes, np.uint8)
        
        # OpenCV ile resmi oku
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            return jsonify({
                "success": False,
                "error": "Resim okunamadı"
            }), 400
        
        # QR kodları bul
        qr_codes = pyzbar.decode(image)
        
        results = []
        for qr_code in qr_codes:
            qr_data = qr_code.data.decode('utf-8')
            app.logger.info(f"QR kod bulundu: {qr_data[:50]}...")
            
            # JSON parse etmeyi dene
            try:
                parsed_data = json.loads(qr_data)
                results.append({
                    "type": "json",
                    "data": parsed_data,
                    "raw": qr_data
                })
            except json.JSONDecodeError:
                # JSON değilse düz text olarak kaydet
                results.append({
                    "type": "text", 
                    "data": qr_data,
                    "raw": qr_data
                })
        
        if not results:
            app.logger.warning("QR kod bulunamadı")
            return jsonify({
                "success": False,
                "error": "QR kod bulunamadı",
                "qr_codes": []
            }), 404
        
        app.logger.info(f"{len(results)} QR kod başarıyla okundu")
        return jsonify({
            "success": True,
            "qr_codes": results,
            "count": len(results)
        })
        
    except Exception as e:
        app.logger.error(f"QR okuma hatası: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Beklenmeyen hata: {str(e)}"
        }), 500

@app.route('/test', methods=['GET'])
def test_endpoint():
    """Test endpoint'i"""
    return jsonify({
        "message": "QR Reader Service çalışıyor",
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "health": "/health",
            "read_qr": "/read-qr (POST)",
            "test": "/test"
        }
    })

if __name__ == '__main__':
    # Logs dizinini oluştur
    os.makedirs('/app/logs', exist_ok=True)
    
    app.logger.info("QR Reader Service başlatılıyor...")
    app.run(host='0.0.0.0', port=5001, debug=False)
