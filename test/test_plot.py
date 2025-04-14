import mplfinance as mpf
import pandas as pd

# Create a small dummy dataset
df = pd.DataFrame({
    "Open": [100, 102, 103, 104, 102],
    "High": [103, 104, 105, 106, 103],
    "Low": [99, 100, 101, 102, 101],
    "Close": [102, 103, 104, 103, 102],
    "Date": pd.date_range(end=pd.Timestamp.today(), periods=5)
})

df.set_index("Date", inplace=True)

# Plot it
mpf.plot(df, type='candle', style='yahoo', title="Test Candles", volume=False)
