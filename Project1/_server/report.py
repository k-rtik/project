# Generate report from dictionary of dataframes
# Dataframe index: DateTime name: time, columns: ticker, price, signal, p/l
from io import StringIO


def get_report(final_data):
    with open('report.csv', 'w') as f:
        with StringIO() as text:
            if final_data is not None:
                final_data.to_csv(text, date_format='%Y-%m-%d-%H:%M')

            # Add space after comma in csv to match format in assessment Word doc
            text.seek(0)
            for line in text.readlines():
                f.write(line.replace(',', ', '))
