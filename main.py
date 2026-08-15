"""
B3 Quote API
============
API REST para consulta de cotações de ações da B3 (Bovespa).

Fonte de dados: Yahoo Finance (via biblioteca yfinance).
Tickers da B3 usam o sufixo ".SA" no Yahoo Finance (ex: PETR4 -> PETR4.SA).
A API adiciona o sufixo automaticamente caso o usuário não o informe.

Autor: Alessandro Dias Borges
"""

import logging
import re
from datetime import datetime, timezone

import yfinance as yf
from fastapi import FastAPI, HTTPException, Path
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Configuração de logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("b3-quote-api")

# ---------------------------------------------------------------------------
# Aplicação FastAPI
# ---------------------------------------------------------------------------
app = FastAPI(
    title="B3 Quote API",
    description=(
        "API REST para consulta de cotações de ações da B3 (Bovespa) "
        "em tempo quase real, utilizando dados do Yahoo Finance."
    ),
    version="1.0.0",
    contact={"name": "Alessandro Dias Borges"},
)

# CORS liberado para facilitar testes acadêmicos (ajuste em produção real)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Modelos de resposta (Pydantic) — geram o schema no Swagger automaticamente
# ---------------------------------------------------------------------------
class HealthResponse(BaseModel):
    status: str = Field(..., example="ok")
    service: str = Field(..., example="b3-quote-api")
    timestamp: str = Field(..., example="2026-08-14T12:00:00+00:00")


class QuoteResponse(BaseModel):
    ticker: str = Field(..., description="Ticker consultado (formato B3)", example="PETR4")
    yahoo_symbol: str = Field(..., description="Símbolo usado no Yahoo Finance", example="PETR4.SA")
    name: str | None = Field(None, description="Nome da empresa", example="Petróleo Brasileiro S.A.")
    currency: str | None = Field(None, example="BRL")
    price: float = Field(..., description="Preço atual (último negócio)", example=38.42)
    previous_close: float | None = Field(None, description="Fechamento anterior", example=38.10)
    change: float | None = Field(None, description="Variação no dia (R$)", example=0.32)
    change_percent: float | None = Field(None, description="Variação no dia (%)", example=0.84)
    day_high: float | None = Field(None, description="Máxima do dia", example=38.75)
    day_low: float | None = Field(None, description="Mínima do dia", example=38.01)
    volume: int | None = Field(None, description="Volume negociado no dia", example=45879300)
    market_state: str | None = Field(None, description="Estado do mercado (OPEN/CLOSED...)", example="OPEN")
    timestamp: str = Field(..., description="Timestamp UTC da consulta", example="2026-08-14T12:00:00+00:00")


class ErrorResponse(BaseModel):
    detail: str = Field(..., example="Ticker 'XXXX9' não encontrado na B3.")


# ---------------------------------------------------------------------------
# Funções auxiliares
# ---------------------------------------------------------------------------
TICKER_PATTERN = re.compile(r"^[A-Z0-9]{4,10}(\.SA)?$")


def normalize_ticker(ticker: str) -> tuple[str, str]:
    """
    Normaliza o ticker informado pelo usuário.

    Retorna uma tupla (ticker_b3, yahoo_symbol).
    Ex.: "petr4" -> ("PETR4", "PETR4.SA")
         "PETR4.SA" -> ("PETR4", "PETR4.SA")
    """
    cleaned = ticker.strip().upper()
    if not TICKER_PATTERN.match(cleaned):
        raise HTTPException(
            status_code=422,
            detail=(
                f"Ticker '{ticker}' possui formato inválido. "
                "Use o formato da B3, ex: PETR4, VALE3, ITUB4."
            ),
        )
    if cleaned.endswith(".SA"):
        return cleaned[:-3], cleaned
    return cleaned, f"{cleaned}.SA"


def fetch_quote(yahoo_symbol: str) -> dict:
    """
    Busca a cotação no Yahoo Finance via yfinance.
    Levanta HTTPException 404 se o ticker não existir,
    ou 502 se houver falha de comunicação com a fonte de dados.
    """
    try:
        asset = yf.Ticker(yahoo_symbol)
        # fast_info é mais leve e rápido que .info
        info = asset.fast_info
        try:
            price = info.get("lastPrice") or info.get("last_price")
        except Exception:
            # Algumas versões do yfinance levantam exceção para ticker inexistente
            price = None
    except ConnectionError as exc:  # falha de rede / API externa
        logger.error("Erro de conexão com Yahoo Finance para %s: %s", yahoo_symbol, exc)
        raise HTTPException(
            status_code=502,
            detail="Falha ao consultar a fonte de dados (Yahoo Finance). Tente novamente.",
        ) from exc
    except Exception as exc:
        logger.error("Erro ao consultar Yahoo Finance para %s: %s", yahoo_symbol, exc)
        raise HTTPException(
            status_code=502,
            detail="Falha ao consultar a fonte de dados (Yahoo Finance). Tente novamente.",
        ) from exc

    if price is None:
        raise HTTPException(
            status_code=404,
            detail=f"Ticker '{yahoo_symbol.removesuffix('.SA')}' não encontrado na B3.",
        )

    # Metadados adicionais (nome da empresa, estado do mercado)
    name = None
    market_state = None
    try:
        meta = asset.get_info()
        name = meta.get("longName") or meta.get("shortName")
        market_state = meta.get("marketState")
    except Exception:
        # Metadados são opcionais — não falha a requisição por causa deles
        logger.warning("Não foi possível obter metadados de %s", yahoo_symbol)

    def safe_get(*keys):
        """Lê uma chave do fast_info sem quebrar caso ela não exista."""
        for key in keys:
            try:
                value = info.get(key)
            except Exception:
                value = None
            if value is not None:
                return value
        return None

    previous_close = safe_get("previousClose", "previous_close")
    change = None
    change_percent = None
    if previous_close:
        change = round(price - previous_close, 4)
        change_percent = round((price - previous_close) / previous_close * 100, 4)

    volume = safe_get("lastVolume", "last_volume")

    return {
        "name": name,
        "currency": safe_get("currency"),
        "price": round(price, 4),
        "previous_close": round(previous_close, 4) if previous_close else None,
        "change": change,
        "change_percent": change_percent,
        "day_high": safe_get("dayHigh", "day_high"),
        "day_low": safe_get("dayLow", "day_low"),
        "volume": int(volume) if volume else None,
        "market_state": market_state,
    }


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@app.get("/health", response_model=HealthResponse, tags=["Infra"])
def health() -> HealthResponse:
    """Verifica se a API está online (usado por monitoramento/load balancer)."""
    return HealthResponse(
        status="ok",
        service="b3-quote-api",
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@app.get(
    "/api/v1/quote/{ticker}",
    response_model=QuoteResponse,
    tags=["Cotações"],
    responses={
        404: {"model": ErrorResponse, "description": "Ticker não encontrado"},
        422: {"model": ErrorResponse, "description": "Formato de ticker inválido"},
        502: {"model": ErrorResponse, "description": "Falha na fonte de dados"},
    },
)
def get_quote(
    ticker: str = Path(..., description="Ticker da B3 (ex: PETR4, VALE3, ITUB4)", example="PETR4"),
) -> QuoteResponse:
    """
    Retorna a cotação atual de uma ação da B3:
    preço atual, variação no dia, máxima, mínima, volume e timestamp.
    """
    ticker_b3, yahoo_symbol = normalize_ticker(ticker)
    logger.info("Consultando cotação de %s (%s)", ticker_b3, yahoo_symbol)
    data = fetch_quote(yahoo_symbol)
    return QuoteResponse(
        ticker=ticker_b3,
        yahoo_symbol=yahoo_symbol,
        timestamp=datetime.now(timezone.utc).isoformat(),
        **data,
    )


# ---------------------------------------------------------------------------
# Execução direta (desenvolvimento): python main.py
# Em produção, use: uvicorn main:app --host 0.0.0.0 --port 8000
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
