# forecasting_service_adapter.py
# Auto-generated adapter for HVDC v2.8.2 pipeline
# This imports functions from the uploaded notebook as a Python module and exposes a stable interface.
from dataclasses import dataclass
import pandas as pd

try:
    import uploaded_nb_module as nbmod
except Exception as e:
    nbmod = None
    _import_error = e

CANDIDATE_FUNCS = []

@dataclass
class ForecastResult:
    df: pd.DataFrame  # columns: date, yhat, yhat_low, yhat_high, model, mape, rmse

class ForecastService:
    def __init__(self, model: str = "auto", horizon: int = 30, conf: float = 0.90):
        self.model = model
        self.horizon = int(horizon)
        self.conf = float(conf)

    def _select_fn(self):
        # 1) If model explicitly matches a function name, prefer it
        if self.model and self.model != "auto":
            if nbmod and hasattr(nbmod, self.model):
                return getattr(nbmod, self.model)
        # 2) Otherwise pick first candidate function from notebook
        if nbmod:
            for name in CANDIDATE_FUNCS:
                if hasattr(nbmod, name):
                    return getattr(nbmod, name)
        return None

    def fit_forecast(self, ts: pd.Series, freq: str = "D") -> ForecastResult:
        if nbmod is None:
            raise ImportError(f"Could not import uploaded_nb_module: {_import_error}")
        fn = self._select_fn()
        if fn is None:
            raise NotImplementedError(f"No forecast-like function found in notebook. Candidates scanned: {CANDIDATE_FUNCS}")

        # Normalize input series
        ts = ts.asfreq(freq).fillna(0)

        # Try common signatures; fallback to keyword variants
        result = None
        last_err = None
        for kwargs in [
            dict(ts=ts, horizon=self.horizon, conf=self.conf),
            dict(series=ts, horizon=self.horizon, conf_int=self.conf),
            dict(ts=ts, steps=self.horizon, alpha=1.0 - self.conf),
            dict(y=ts, periods=self.horizon, conf=self.conf),
            dict(y=ts, steps=self.horizon)
        ]:
            try:
                out = fn(**kwargs)
                result = out
                break
            except TypeError as e:
                last_err = e
                continue

        if result is None:
            # Final attempt: positional (ts, horizon, conf)
            try:
                result = fn(ts, self.horizon, self.conf)
            except Exception as e:
                raise RuntimeError(f"Unable to call forecast function '{fn.__name__}' with tried signatures. Last error: {last_err}; final: {e}")

        # Coerce output to DataFrame with standard columns
        if isinstance(result, pd.DataFrame):
            df = result.copy()
        elif isinstance(result, (list, tuple)):
            # Expect (yhat, yhat_low, yhat_high) or (df, metrics)
            try:
                if len(result) >= 3 and all(hasattr(x, '__len__') for x in result[:3]):
                    df = pd.DataFrame({
                        "date": pd.date_range(ts.index.max() + pd.Timedelta(1, unit=freq), periods=self.horizon, freq=freq),
                        "yhat": result[0],
                        "yhat_low": result[1],
                        "yhat_high": result[2],
                    })
                else:
                    df = pd.DataFrame(result[0])
            except Exception:
                df = pd.DataFrame(result)
        else:
            # Attempt to convert to Series/DataFrame
            try:
                df = pd.DataFrame({"yhat": pd.Series(result)}).reset_index(drop=True)
                df["date"] = pd.date_range(ts.index.max() + pd.Timedelta(1, unit=freq), periods=len(df), freq=freq)
            except Exception as e:
                raise ValueError(f"Unrecognized forecast output type: {type(result)}; error: {e}")

        # Ensure standard columns
        if "date" not in df.columns:
            df["date"] = pd.date_range(ts.index.max() + pd.Timedelta(1, unit=freq), periods=len(df), freq=freq)
        for col in ["yhat", "yhat_low", "yhat_high"]:
            if col not in df.columns:
                df[col] = None
        if "model" not in df.columns:
            df["model"] = getattr(fn, "__name__", "notebook_fn")
        if "mape" not in df.columns:
            df["mape"] = None
        if "rmse" not in df.columns:
            df["rmse"] = None

        return ForecastResult(df=df[["date","yhat","yhat_low","yhat_high","model","mape","rmse"]])

    def forecast_pkg_stock(self, df_io: pd.DataFrame, key_cols=("warehouse", "site")) -> pd.DataFrame:
        rows = []
        for key, g in df_io.groupby(list(key_cols)):
            ts = g.set_index("date")["stock_pkg"].sort_index()
            res = self.fit_forecast(ts)
            out = res.df.assign(**{k:v for k, v in zip(key_cols, key)})
            rows.append(out)
        return pd.concat(rows, ignore_index=True)
