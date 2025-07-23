"""
Data processing service with processing bugs for testing incident detection.
"""

import random
import time
import os
import json
from typing import Dict, Any, Optional, List
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .base_service import BaseService
from ..logging_system import StructuredLogger
from ..config import TestConfig


class DataProcessingService(BaseService):
    """
    Data processing service with intentional processing bugs for testing.
    
    Contains three specific bugs:
    1. FileNotFoundError in process_batch() - missing file
    2. ValueError in transform_data() - invalid conversion
    3. MemoryError in aggregate_results() - simulated memory error
    """
    
    def __init__(self, logger: StructuredLogger, config: Optional[TestConfig] = None):
        super().__init__("DataProcessingService", logger, error_probability=0.07, config=config)
        
        # Mock data storage
        self.data_batches = {}
        self.processed_results = {}
        
        # Mock data sources
        self.data_sources = {
            "source1": {
                "type": "csv",
                "path": "/data/source1/",
                "batch_size": 100
            },
            "source2": {
                "type": "json",
                "path": "/data/source2/",
                "batch_size": 50
            },
            "source3": {
                "type": "xml",
                "path": "/data/source3/",
                "batch_size": 200
            }
        }
        
        # Initialize with some sample data
        self._initialize_sample_data()
    
    def _initialize_sample_data(self):
        """Initialize with some sample data batches."""
        for i in range(1, 4):
            batch_id = f"batch_{i}"
            self.data_batches[batch_id] = {
                "id": batch_id,
                "source": f"source{i}",
                "records": [{"id": j, "value": random.randint(1, 100)} for j in range(1, 11)],
                "created_at": time.time() - random.randint(100, 1000)
            }
    
    def get_service_name(self) -> str:
        """Get the service name."""
        return "DataProcessingService"
    
    def get_available_operations(self) -> list:
        """Get list of available operations."""
        return ["process_batch", "transform_data", "aggregate_results"]
    
    def process_batch(self, batch_id: str, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process a data batch with FileNotFoundError bug.
        
        Bug: Tries to open a non-existent file
        """
        def normal_operation():
            # Check if batch exists
            if batch_id not in self.data_batches:
                return {
                    "success": False,
                    "message": f"Batch {batch_id} not found"
                }
            
            batch = self.data_batches[batch_id]
            
            # Process the batch
            processed_records = []
            for record in batch["records"]:
                processed_record = {
                    "id": record["id"],
                    "original_value": record["value"],
                    "processed_value": record["value"] * 2,  # Simple processing
                    "processed_at": time.time()
                }
                processed_records.append(processed_record)
            
            # Store the results
            result_id = f"result_{batch_id}_{int(time.time())}"
            self.processed_results[result_id] = {
                "batch_id": batch_id,
                "records": processed_records,
                "processed_at": time.time(),
                "record_count": len(processed_records)
            }
            
            return {
                "success": True,
                "result_id": result_id,
                "record_count": len(processed_records),
                "message": f"Successfully processed batch {batch_id}"
            }
        
        def error_operation():
            # Check if batch exists
            if batch_id not in self.data_batches:
                return {
                    "success": False,
                    "message": f"Batch {batch_id} not found"
                }
            
            batch = self.data_batches[batch_id]
            
            # BUG: FileNotFoundError - tries to open a non-existent file
            # This simulates a bug where the code tries to read additional data
            # from a file that doesn't exist
            batch_source = batch["source"]
            source_info = self.data_sources.get(batch_source, {})
            source_path = source_info.get("path", "/unknown/path/")
            
            # Construct a path to a file that doesn't exist
            non_existent_file = f"{source_path}batch_{batch_id}_metadata.json"
            
            # Try to open the non-existent file
            with open(non_existent_file, 'r') as f:  # FileNotFoundError
                metadata = json.load(f)
            
            # The code below won't execute due to the exception
            processed_records = []
            for record in batch["records"]:
                processed_record = {
                    "id": record["id"],
                    "original_value": record["value"],
                    "processed_value": record["value"] * 2,
                    "processed_at": time.time()
                }
                processed_records.append(processed_record)
            
            result_id = f"result_{batch_id}_{int(time.time())}"
            self.processed_results[result_id] = {
                "batch_id": batch_id,
                "records": processed_records,
                "processed_at": time.time(),
                "record_count": len(processed_records)
            }
            
            return {
                "success": True,
                "result_id": result_id,
                "record_count": len(processed_records),
                "message": f"Successfully processed batch {batch_id}"
            }
        
        return self._execute_with_error_handling(
            "process_batch",
            normal_operation,
            error_operation,
            batch_id=batch_id,
            options=options
        )
    
    def transform_data(self, data: List[Dict[str, Any]], transformation_type: str) -> Dict[str, Any]:
        """
        Transform data with ValueError bug.
        
        Bug: Tries to convert a string to an integer when it contains non-numeric characters
        """
        def normal_operation():
            if not data:
                return {
                    "success": False,
                    "message": "No data provided for transformation"
                }
            
            # Apply transformation based on type
            transformed_data = []
            
            if transformation_type == "numeric":
                for item in data:
                    transformed_item = {**item}
                    if "value" in item:
                        transformed_item["value"] = float(item["value"]) * 1.5
                    transformed_data.append(transformed_item)
            
            elif transformation_type == "text":
                for item in data:
                    transformed_item = {**item}
                    if "text" in item:
                        transformed_item["text"] = item["text"].upper()
                    transformed_data.append(transformed_item)
            
            elif transformation_type == "boolean":
                for item in data:
                    transformed_item = {**item}
                    if "active" in item:
                        transformed_item["active"] = not item["active"]
                    transformed_data.append(transformed_item)
            
            else:
                return {
                    "success": False,
                    "message": f"Unknown transformation type: {transformation_type}"
                }
            
            return {
                "success": True,
                "transformed_data": transformed_data,
                "item_count": len(transformed_data),
                "transformation_type": transformation_type
            }
        
        def error_operation():
            if not data:
                return {
                    "success": False,
                    "message": "No data provided for transformation"
                }
            
            # BUG: ValueError - invalid conversion
            # This simulates a bug where the code tries to convert a string with
            # non-numeric characters to an integer
            transformed_data = []
            
            if transformation_type == "numeric":
                for item in data:
                    transformed_item = {**item}
                    if "value" in item:
                        # Simulate a case where the value might be a string with non-numeric characters
                        if isinstance(item["value"], str) and not item["value"].isdigit():
                            # This will raise ValueError for strings like "abc" or "12.3"
                            transformed_item["value"] = int(item["value"]) * 2  # ValueError
                        else:
                            transformed_item["value"] = float(item["value"]) * 1.5
                    transformed_data.append(transformed_item)
            
            elif transformation_type == "text":
                for item in data:
                    transformed_item = {**item}
                    if "text" in item:
                        transformed_item["text"] = item["text"].upper()
                    transformed_data.append(transformed_item)
            
            elif transformation_type == "boolean":
                for item in data:
                    transformed_item = {**item}
                    if "active" in item:
                        transformed_item["active"] = not item["active"]
                    transformed_data.append(transformed_item)
            
            else:
                return {
                    "success": False,
                    "message": f"Unknown transformation type: {transformation_type}"
                }
            
            return {
                "success": True,
                "transformed_data": transformed_data,
                "item_count": len(transformed_data),
                "transformation_type": transformation_type
            }
        
        return self._execute_with_error_handling(
            "transform_data",
            normal_operation,
            error_operation,
            data_count=len(data),
            transformation_type=transformation_type
        )
    
    def aggregate_results(self, result_ids: List[str], aggregation_method: str = "sum") -> Dict[str, Any]:
        """
        Aggregate processing results with simulated MemoryError bug.
        
        Bug: Simulates a memory error during aggregation of large datasets
        """
        def normal_operation():
            if not result_ids:
                return {
                    "success": False,
                    "message": "No result IDs provided for aggregation"
                }
            
            # Collect all results
            all_records = []
            for result_id in result_ids:
                if result_id in self.processed_results:
                    all_records.extend(self.processed_results[result_id]["records"])
            
            if not all_records:
                return {
                    "success": False,
                    "message": "No valid results found for aggregation"
                }
            
            # Perform aggregation
            if aggregation_method == "sum":
                total = sum(record["processed_value"] for record in all_records if "processed_value" in record)
                aggregated_value = total
            
            elif aggregation_method == "average":
                values = [record["processed_value"] for record in all_records if "processed_value" in record]
                aggregated_value = sum(values) / len(values) if values else 0
            
            elif aggregation_method == "max":
                values = [record["processed_value"] for record in all_records if "processed_value" in record]
                aggregated_value = max(values) if values else 0
            
            elif aggregation_method == "min":
                values = [record["processed_value"] for record in all_records if "processed_value" in record]
                aggregated_value = min(values) if values else 0
            
            else:
                return {
                    "success": False,
                    "message": f"Unknown aggregation method: {aggregation_method}"
                }
            
            return {
                "success": True,
                "aggregation_method": aggregation_method,
                "aggregated_value": aggregated_value,
                "record_count": len(all_records),
                "result_ids": result_ids
            }
        
        def error_operation():
            if not result_ids:
                return {
                    "success": False,
                    "message": "No result IDs provided for aggregation"
                }
            
            # BUG: Simulated MemoryError
            # This simulates a memory error that might occur when processing large datasets
            
            # First, collect all results (this part works fine)
            all_records = []
            for result_id in result_ids:
                if result_id in self.processed_results:
                    all_records.extend(self.processed_results[result_id]["records"])
            
            if not all_records:
                return {
                    "success": False,
                    "message": "No valid results found for aggregation"
                }
            
            # Simulate a memory-intensive operation that fails
            if len(all_records) > 0:
                # Create a condition that always triggers the error for testing purposes
                # In a real scenario, this might only happen with very large datasets
                
                # Simulate trying to create a massive array that exceeds memory
                try:
                    # This is a safer way to simulate a MemoryError without actually
                    # trying to allocate too much memory, which could crash the process
                    raise MemoryError("Simulated memory error during data aggregation")
                except MemoryError as e:
                    # Re-raise the exception to be caught by the error handling mechanism
                    raise e
            
            # The code below won't execute due to the exception
            if aggregation_method == "sum":
                total = sum(record["processed_value"] for record in all_records if "processed_value" in record)
                aggregated_value = total
            
            elif aggregation_method == "average":
                values = [record["processed_value"] for record in all_records if "processed_value" in record]
                aggregated_value = sum(values) / len(values) if values else 0
            
            else:
                return {
                    "success": False,
                    "message": f"Unknown aggregation method: {aggregation_method}"
                }
            
            return {
                "success": True,
                "aggregation_method": aggregation_method,
                "aggregated_value": aggregated_value,
                "record_count": len(all_records),
                "result_ids": result_ids
            }
        
        return self._execute_with_error_handling(
            "aggregate_results",
            normal_operation,
            error_operation,
            result_count=len(result_ids),
            aggregation_method=aggregation_method
        )
    
    def get_available_batches(self) -> Dict[str, Any]:
        """Get information about available data batches."""
        return {
            "total_batches": len(self.data_batches),
            "batches": list(self.data_batches.keys())
        }
    
    def get_batch_details(self, batch_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific batch."""
        if batch_id not in self.data_batches:
            return {
                "success": False,
                "message": f"Batch {batch_id} not found"
            }
        
        batch = self.data_batches[batch_id]
        return {
            "success": True,
            "batch_id": batch_id,
            "source": batch["source"],
            "record_count": len(batch["records"]),
            "created_at": batch["created_at"]
        }
    
    def get_processing_results(self) -> Dict[str, Any]:
        """Get information about processing results."""
        return {
            "total_results": len(self.processed_results),
            "results": list(self.processed_results.keys())
        }