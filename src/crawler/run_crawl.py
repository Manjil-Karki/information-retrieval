import os
import sys
import argparse
import time
from datetime import datetime

from src.core.config import (
    TARGET_URL,
    DATA_PATH,
    DATA_JSON,
    PROCESSED_DOCUMENTS,
    INDEX_PATH,
)



import asyncio
from src.crawler.scraper import main as scraper_main


class ResearcherScraper:
    
    def __init__(self, target_url=None, incremental=True):
        self.incremental = incremental
    
    def scrape_all(self, output_file="data.json"):
        asyncio.run(scraper_main())




def print_banner(text, char="="):
    width = 80
    print("\n" + char * width)
    print(text.center(width))
    print(char * width + "\n")


def print_step(step_num, total_steps, description):
    print(f"\n{'='*80}")
    print(f"STEP {step_num}/{total_steps}: {description}")
    print(f"{'='*80}\n")


def run_scraper(target_url, output_file):
    try:
        
        print(f"Target URL: {target_url}")
        print(f"Output file: {output_file}")
        
        scraper = ResearcherScraper(target_url)
        scraper.scrape_all(output_file=output_file)
        
        if os.path.exists(output_file):
            file_size = os.path.getsize(output_file) / 1024
            print(f"\nScraping completed successfully!")
            print(f"File size: {file_size:.2f} KB")
            return True
        else:
            print(f"\nError: Output file not created")
            return False
            
    except Exception as e:
        print(f"\nScraping failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_preprocessor(input_file, output_file):
    try:
        from src.crawler.preprocessor import PublicationPreprocessor
        
        print(f"Input file: {input_file}")
        print(f"Output file: {output_file}")
        
        if not os.path.exists(input_file):
            print(f"\nError: Input file not found: {input_file}")
            return False
        
        preprocessor = PublicationPreprocessor(input_file)
        preprocessor.save(output_file)
        
        if os.path.exists(output_file):
            file_size = os.path.getsize(output_file) / 1024
            print(f"File size: {file_size:.2f} KB")
            return True
        else:
            print(f"\nError: Output file not created")
            return False
            
    except Exception as e:
        print(f"\nPreprocessing failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_indexer(input_file, output_file):
    try:
        from src.crawler.indexer import build_index_from_file
        
        print(f"Input file: {input_file}")
        print(f"Output file: {output_file}")
        
        if not os.path.exists(input_file):
            print(f"\nError: Input file not found: {input_file}")
            return False
        
        build_index_from_file(input_file, output_file)
        
        if os.path.exists(output_file):
            file_size = os.path.getsize(output_file) / 1024
            print(f"File size: {file_size:.2f} KB")
            return True
        else:
            print(f"\nError: Output file not created")
            return False
            
    except Exception as e:
        print(f"\nIndexing failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def verify_index(index_file):
    try:
        from src.services.search_engine import SearchEngine
        
        print(f"\nVerifying index: {index_file}")
        
        engine = SearchEngine(index_file)
        
        test_query = "machine learning"
        results = engine.search(test_query, top_n=3)
        
        print(f"\nIndex verification successful!")
        print(f"Test query: '{test_query}'")
        print(f"Found {len(results)} results")
        
        if results:
            print("\nTop 3 results:")
            for i, (doc_id, score, doc) in enumerate(results, 1):
                title = doc['title'][:60] + "..." if len(doc['title']) > 60 else doc['title']
                print(f"  {i}. [{score:.4f}] {title}")
        
        return True
        
    except Exception as e:
        print(f"\nIndex verification failed: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Run complete crawling and indexing pipeline"
    )
    parser.add_argument(
        "--url",
        type=str,
        default=TARGET_URL,
        help="Target URL to scrape"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=DATA_PATH,
        help="Output directory for all files"
    )
    parser.add_argument(
        "--skip-scrape",
        action="store_true",
        help="Skip scraping step (use existing raw data)"
    )
    parser.add_argument(
        "--skip-preprocess",
        action="store_true",
        help="Skip preprocessing step (use existing processed data)"
    )
    
    args = parser.parse_args()
    
    os.makedirs(args.output_dir, exist_ok=True)
    
    raw_data_file = str(DATA_JSON)
    processed_data_file = str(PROCESSED_DOCUMENTS)
    index_file = str(INDEX_PATH)
    
    print_banner("RESEARCH PUBLICATION CRAWLER & INDEXER")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Output directory: {args.output_dir}")
    
    start_time = time.time()
    
    total_steps = 3
    if args.skip_scrape:
        total_steps -= 1
    if args.skip_preprocess:
        total_steps -= 1
    
    current_step = 0
    
    if not args.skip_scrape:
        current_step += 1
        print_step(current_step, total_steps, "Web Scraping")
        
        if not run_scraper(args.url, raw_data_file):
            print("\nPipeline failed at scraping step")
            sys.exit(1)
    else:
        print("\nSkipping scraping step (using existing data)")
        if not os.path.exists(raw_data_file):
            print(f"Error: Raw data file not found: {raw_data_file}")
            sys.exit(1)
    
    if not args.skip_preprocess:
        current_step += 1
        print_step(current_step, total_steps, "Data Preprocessing")
        
        if not run_preprocessor(raw_data_file, processed_data_file):
            print("\nPipeline failed at preprocessing step")
            sys.exit(1)
    else:
        print("\nSkipping preprocessing step (using existing data)")
        if not os.path.exists(processed_data_file):
            print(f"Error: Processed data file not found: {processed_data_file}")
            sys.exit(1)
    
    current_step += 1
    print_step(current_step, total_steps, "Index Building")
    
    if not run_indexer(processed_data_file, index_file):
        print("\nPipeline failed at indexing step")
        sys.exit(1)
    
    print_banner("VERIFICATION", char="-")
    verify_index(index_file)
    
    elapsed_time = time.time() - start_time
    minutes = int(elapsed_time // 60)
    seconds = int(elapsed_time % 60)
    
    print_banner("PIPELINE COMPLETED SUCCESSFULLY", char="=")
    print(f"Total time: {minutes}m {seconds}s")
    print(f"Output files:")
    print(f"  - Raw data:       {raw_data_file}")
    print(f"  - Processed data: {processed_data_file}")
    print(f"  - Index file:     {index_file}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nPipeline interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)