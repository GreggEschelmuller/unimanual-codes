import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

data = pd.read_csv("data/P99/p99_Baseline.csv")

sns.set_palette("pastel")

fig = sns.pointplot(
    data=data,
    x="vibration",
    y="error",
    hue="vibration",
    legend=False,
)

fig.set_xticklabels(["No vibration", "Dual", "Biceps", "Triceps"])
plt.show()
