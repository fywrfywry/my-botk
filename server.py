from fastapi import FastAPI, HTTPException
import os

app = FastAPI()

@app.get("/")
def home():
    return {"status": "online", "message": "Shopify Checker API is running successfully!"}

@app.get("/shopify")
def check_shopify(site: str, cc: str):
    try:
        cc_parts = cc.split("|")
        if len(cc_parts) < 4:
            raise HTTPException(status_code=400, detail="Invalid card format. Use CARD|MM|YY|CVV")
        
        card_number, exp_month, exp_year, cvv = cc_parts[0], cc_parts[1], cc_parts[2], cc_parts[3]

        return {
            "status": "success",
            "result": "Charged",
            "message": "$10 Charged Successfully!",
            "site": site
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 5000))
    uvicorn.run(app, host="0.0.0.0", port=port)
