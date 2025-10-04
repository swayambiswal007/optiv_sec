# src/main.py - Universal File Cleanser Main Application
import os
import sys
import json
import time
from pathlib import Path
from typing import List, Dict
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

from .config import Config
from .universal_processor import UniversalFileProcessor
from .text_cleaner import TextCleaner
from .sensitive_detector import SensitiveDataDetector

class UniversalFileCleanser:
    """Universal file cleanser supporting all document types"""
    
    def __init__(self):
        self.processor = UniversalFileProcessor()
        self.text_cleaner = TextCleaner()
        self.sensitive_detector = SensitiveDataDetector()
        
        # Ensure directories exist
        for directory in [Config.INPUT_DIR, Config.OUTPUT_DIR, Config.TEMP_DIR, Config.LOG_DIR]:
            os.makedirs(directory, exist_ok=True)
        
        # Statistics
        self.stats = {
            'total_files': 0,
            'files_processed': 0,
            'files_failed': 0,
            'files_skipped': 0,
            'by_type': {},
            'sensitive_items_found': 0,
            'processing_time': 0,
            'errors': []
        }
    
    def process_directory(self, input_dir: str = None, recursive: bool = False) -> Dict:
        """Process all files in a directory"""
        if input_dir is None:
            input_dir = Config.INPUT_DIR
        
        files = self._get_files_from_directory(input_dir, recursive)
        return self.process_files(files)
    
    def process_files(self, file_paths: List[str]) -> Dict:
        """Process multiple files with progress tracking"""
        start_time = time.time()
        
        self.stats['total_files'] = len(file_paths)
        
        if not file_paths:
            print("❌ No files to process")
            return self.stats
        
        print("🧹 Universal File Cleanser")
        print("=" * 70)
        print(f"📂 Input: {Config.INPUT_DIR}")
        print(f"📂 Output: {Config.OUTPUT_DIR}")
        print(f"📋 Files to process: {len(file_paths)}")
        print(f"🔧 Mode: {Config.REDACTION_MODE} (intensity: {Config.BLUR_INTENSITY})")
        print("=" * 70)
        
        # Group files by type
        files_by_type = self._group_files_by_type(file_paths)
        
        print("\n📊 File types detected:")
        for file_type, files in files_by_type.items():
            print(f"   {file_type}: {len(files)} file(s)")
        
        print("\n🚀 Starting processing...")
        print("-" * 70)
        
        # Process files
        if Config.USE_MULTITHREADING and len(file_paths) > 1:
            results = self._process_files_parallel(file_paths)
        else:
            results = self._process_files_sequential(file_paths)
        
        # Calculate statistics
        self.stats['processing_time'] = time.time() - start_time
        
        # Print summary
        self._print_summary()
        
        # Save processing report
        if Config.GENERATE_SUMMARY_REPORT:
            self._save_report()
        
        return self.stats
    
    def _process_files_sequential(self, file_paths: List[str]) -> List[Dict]:
        """Process files one by one"""
        results = []
        
        for i, file_path in enumerate(file_paths, 1):
            print(f"\n[{i}/{len(file_paths)}] 📄 {Path(file_path).name}")
            print("-" * 40)
            
            result = self._process_single_file(file_path)
            results.append(result)
        
        return results
    
    def _process_files_parallel(self, file_paths: List[str]) -> List[Dict]:
        """Process files in parallel"""
        results = []
        
        with ThreadPoolExecutor(max_workers=Config.MAX_WORKERS) as executor:
            future_to_file = {executor.submit(self._process_single_file, fp): fp for fp in file_paths}
            
            for i, future in enumerate(as_completed(future_to_file), 1):
                file_path = future_to_file[future]
                print(f"\n[{i}/{len(file_paths)}] 📄 {Path(file_path).name}")
                
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    print(f"❌ Error: {str(e)}")
                    self.stats['files_failed'] += 1
                    self.stats['errors'].append({
                        'file': file_path,
                        'error': str(e)
                    })
        
        return results
    
    def _process_single_file(self, file_path: str) -> Dict:
        """Process a single file"""
        file_path = Path(file_path)
        
        try:
            # Check file size
            file_size_mb = file_path.stat().st_size / (1024 * 1024)
            if file_size_mb > Config.MAX_FILE_SIZE_MB:
                print(f"⚠️  File too large: {file_size_mb:.2f} MB (max: {Config.MAX_FILE_SIZE_MB} MB)")
                self.stats['files_skipped'] += 1
                return {'status': 'skipped', 'reason': 'file_too_large'}
            
            # Detect file type
            file_type = self.processor.detect_file_type(str(file_path))
            print(f"🔍 Type: {file_type}")
            print(f"📏 Size: {file_size_mb:.2f} MB")
            
            # Process based on type
            result = self.processor.process_file(
                str(file_path),
                self.sensitive_detector,
                self.text_cleaner
            )
            
            # Update statistics
            self.stats['files_processed'] += 1
            self.stats['by_type'][file_type] = self.stats['by_type'].get(file_type, 0) + 1
            
            sensitive_count = len(result.get('sensitive_items', []))
            self.stats['sensitive_items_found'] += sensitive_count
            
            # Print results
            if sensitive_count > 0:
                print(f"🚨 Sensitive items found: {sensitive_count}")
                
                # Show first few sensitive items
                items_to_show = min(5, sensitive_count)
                print(f"   Top {items_to_show} sensitive items:")
                for i, item in enumerate(result['sensitive_items'][:items_to_show], 1):
                    item_text = item['text'][:30] + '...' if len(item['text']) > 30 else item['text']
                    print(f"      {i}. {item['type']}: '{item_text}'")
                
                if sensitive_count > items_to_show:
                    print(f"      ... and {sensitive_count - items_to_show} more")
            else:
                print(f"✅ No sensitive data detected")
            
            # Print output files
            if result.get('output_files'):
                print(f"📁 Output files created: {len(result['output_files'])}")
                for output_file in result['output_files']:
                    file_size = Path(output_file).stat().st_size if Path(output_file).exists() else 0
                    print(f"   📄 {Path(output_file).name} ({file_size:,} bytes)")
            
            # Save metadata
            if Config.SAVE_METADATA:
                self._save_file_metadata(file_path, result)
            
            print(f"✅ Completed: {file_path.name}")
            
            result['status'] = 'success'
            return result
            
        except Exception as e:
            print(f"❌ Failed: {str(e)}")
            self.stats['files_failed'] += 1
            self.stats['errors'].append({
                'file': str(file_path),
                'error': str(e)
            })
            
            if Config.DEBUG_MODE:
                import traceback
                traceback.print_exc()
            
            return {'status': 'failed', 'error': str(e)}
    
    def _get_files_from_directory(self, directory: str, recursive: bool = False) -> List[str]:
        """Get all supported files from directory"""
        files = []
        
        path = Path(directory)
        
        if not path.exists():
            print(f"❌ Directory not found: {directory}")
            return files
        
        if recursive:
            pattern = '**/*'
        else:
            pattern = '*'
        
        for file_path in path.glob(pattern):
            if file_path.is_file() and Config.is_supported_file(str(file_path)):
                files.append(str(file_path))
        
        return sorted(files)
    
    def _group_files_by_type(self, file_paths: List[str]) -> Dict[str, List[str]]:
        """Group files by their type"""
        grouped = {}
        
        for file_path in file_paths:
            file_type = self.processor.detect_file_type(file_path)
            if file_type not in grouped:
                grouped[file_type] = []
            grouped[file_type].append(file_path)
        
        return grouped
    
    def _save_file_metadata(self, file_path: Path, result: Dict):
        """Save metadata for a processed file"""
        metadata = {
            'input_file': str(file_path),
            'file_type': result.get('file_type', 'unknown'),
            'processed_at': datetime.now().isoformat(),
            'file_size': file_path.stat().st_size,
            'sensitive_items_found': len(result.get('sensitive_items', [])),
            'sensitive_types': list(set([item['type'] for item in result.get('sensitive_items', [])])),
            'output_files': result.get('output_files', []),
            'redaction_applied': result.get('redaction_applied', False),
            'document_type': result.get('document_type', 'unknown'),
            'config': {
                'redaction_mode': Config.REDACTION_MODE,
                'blur_intensity': Config.BLUR_INTENSITY,
            }
        }
        
        metadata_path = Path(Config.OUTPUT_DIR) / f"{file_path.stem}_metadata.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    def _save_report(self):
        """Save processing report"""
        report = {
            'generated_at': datetime.now().isoformat(),
            'summary': {
                'total_files': self.stats['total_files'],
                'files_processed': self.stats['files_processed'],
                'files_failed': self.stats['files_failed'],
                'files_skipped': self.stats['files_skipped'],
                'success_rate': f"{(self.stats['files_processed'] / self.stats['total_files'] * 100):.2f}%" if self.stats['total_files'] > 0 else "0%",
                'sensitive_items_found': self.stats['sensitive_items_found'],
                'processing_time_seconds': round(self.stats['processing_time'], 2),
            },
            'by_file_type': self.stats['by_type'],
            'errors': self.stats['errors'],
            'configuration': {
                'redaction_mode': Config.REDACTION_MODE,
                'blur_intensity': Config.BLUR_INTENSITY,
                'supported_formats': len(Config.SUPPORTED_FORMATS),
                'sensitive_patterns': len(Config.SENSITIVE_PATTERNS),
            }
        }
        
        report_path = Path(Config.OUTPUT_DIR) / f"processing_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n📋 Report saved: {report_path}")
    
    def _print_summary(self):
        """Print comprehensive processing summary"""
        print("\n" + "=" * 70)
        print("📊 PROCESSING SUMMARY")
        print("=" * 70)
        print(f"📂 Total files: {self.stats['total_files']}")
        print(f"✅ Successfully processed: {self.stats['files_processed']}")
        print(f"❌ Failed: {self.stats['files_failed']}")
        print(f"⏭️  Skipped: {self.stats['files_skipped']}")
        
        if self.stats['total_files'] > 0:
            success_rate = (self.stats['files_processed'] / self.stats['total_files']) * 100
            print(f"📈 Success rate: {success_rate:.1f}%")
        
        print(f"\n🚨 Sensitive items detected: {self.stats['sensitive_items_found']}")
        print(f"⏱️  Processing time: {self.stats['processing_time']:.2f} seconds")
        
        if self.stats['by_type']:
            print(f"\n📊 Files processed by type:")
            for file_type, count in sorted(self.stats['by_type'].items()):
                print(f"   {file_type}: {count}")
        
        if self.stats['errors']:
            print(f"\n❌ Errors ({len(self.stats['errors'])}):")
            for error in self.stats['errors'][:5]:  # Show first 5 errors
                print(f"   • {Path(error['file']).name}: {error['error']}")
            
            if len(self.stats['errors']) > 5:
                print(f"   ... and {len(self.stats['errors']) - 5} more")
        
        # List output directory
        output_files = list(Path(Config.OUTPUT_DIR).glob('*'))
        if output_files:
            print(f"\n📁 Output directory: {Config.OUTPUT_DIR}")
            print(f"   Total files: {len(output_files)}")
            
            # Calculate total size
            total_size = sum(f.stat().st_size for f in output_files if f.is_file())
            print(f"   Total size: {total_size / (1024*1024):.2f} MB")
        
        print("=" * 70)
        
        if self.stats['files_processed'] > 0:
            print("✨ Processing complete! Check the output directory for redacted files.")
        else:
            print("⚠️  No files were processed successfully.")

def main():
    """Main entry point"""
    print("🧹 Universal File Cleanser")
    print("🔒 Automated Sensitive Data Redaction System")
    print("=" * 70)
    print("Supported formats: Images, PDFs, Excel, CSV, JSON, XML, Text, Logs")
    print("Detects: Aadhaar, PAN, Credit Cards, Emails, Phones, IPs, and more")
    print("=" * 70)
    
    try:
        cleanser = UniversalFileCleanser()
        
        if len(sys.argv) > 1:
            # Process specific files
            file_paths = []
            for arg in sys.argv[1:]:
                if os.path.isfile(arg):
                    file_paths.append(arg)
                elif os.path.isdir(arg):
                    # Process entire directory
                    dir_files = cleanser._get_files_from_directory(arg, recursive=False)
                    file_paths.extend(dir_files)
                else:
                    print(f"⚠️  Not found: {arg}")
            
            if file_paths:
                print(f"\n🎯 Processing {len(file_paths)} specified file(s)")
                cleanser.process_files(file_paths)
            else:
                print("❌ No valid files or directories specified")
        
        else:
            # Process all files in input directory
            print(f"\n🔍 Processing all files in: {Config.INPUT_DIR}")
            cleanser.process_directory()
    
    except KeyboardInterrupt:
        print(f"\n\n⏹️  Processing interrupted by user")
    
    except Exception as e:
        print(f"\n💥 Unexpected error: {str(e)}")
        if Config.DEBUG_MODE:
            import traceback
            traceback.print_exc()
    
    print("\n✨ File Cleanser finished!")
    print(f"📁 Check the output directory: {Config.OUTPUT_DIR}")

if __name__ == "__main__":
    main()