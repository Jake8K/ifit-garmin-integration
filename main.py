from ifitscraper import ifitScraper
from garminuploader import garminUploader
import os

if __name__ == "__main__":
    cwd = os.getcwd()
    dl_dir = os.path.join(cwd, "tmp", "csv")
    ul_dir = os.path.join(cwd, "tmp", "tcx")

    # get workout csv files
    scraper = ifitScraper(debug=True, dl_dir=dl_dir)
    scraper.find_and_download_csv_files()  # TODO: add pagination, latest, and date ranges

    # transform csv files into tcx files
    # TODO: make tcx -> csv converter class

    # upload to garmin connect
    garmin = garminUploader(debug=True)
    garmin.drag_and_drop_file(ul_dir)

    scraper.finish()
    garmin.finish()
