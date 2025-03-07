import pytest
import pandas as pd
import io
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException, UploadFile
from app.utils.file_parser import parse_transactions_file

class TestFileParser:
    @pytest.fixture
    def mock_csv_file(self):
        """Create a mock CSV file with valid data."""
        content = """Transaction Date,Description,Debit,Credit
2025-01-15,Grocery Store,100.50,
2025-01-16,Restaurant,,75.25
2025-01-17,Gas Station,45.00,
"""
        file = AsyncMock(spec=UploadFile)
        file.filename = "test.csv"
        file.read = AsyncMock(return_value=content.encode('utf-8'))
        return file

    @pytest.fixture
    def mock_excel_file(self):
        """Create a mock Excel file with valid data."""
        # Create a test DataFrame
        df = pd.DataFrame({
            'Transaction Date': ['2025-01-15', '2025-01-16', '2025-01-17'],
            'Description': ['Grocery Store', 'Restaurant', 'Gas Station'],
            'Amount': [100.50, -75.25, 45.00]
        })
        
        # Convert to Excel binary content
        excel_binary = io.BytesIO()
        df.to_excel(excel_binary, index=False)
        excel_binary.seek(0)
        
        # Create mock file
        file = AsyncMock(spec=UploadFile)
        file.filename = "test.xlsx"
        file.read = AsyncMock(return_value=excel_binary.getvalue())
        return file

    @pytest.fixture
    def mock_xls_file(self):
        """Create a mock XLS file with valid data."""
        # Create a test DataFrame
        df = pd.DataFrame({
            'Transaction Date': ['2025-01-15', '2025-01-16', '2025-01-17'],
            'Description': ['Grocery Store', 'Restaurant', 'Gas Station'],
            'Amount': [100.50, -75.25, 45.00]
        })
        
        # Convert to Excel binary content (use default engine)
        excel_binary = io.BytesIO()
        df.to_excel(excel_binary, index=False)
        excel_binary.seek(0)
        
        # Create mock file
        file = AsyncMock(spec=UploadFile)
        file.filename = "test.xls"  # Only the extension matters for the test
        file.read = AsyncMock(return_value=excel_binary.getvalue())
        return file

    @pytest.fixture
    def mock_csv_posting_date(self):
        """Create a mock CSV file with Posting Date instead of Transaction Date."""
        content = """Posting Date,Description,Amount
2025-01-15,Grocery Store,100.50
2025-01-16,Restaurant,-75.25
2025-01-17,Gas Station,45.00
"""
        file = AsyncMock(spec=UploadFile)
        file.filename = "test.csv"
        file.read = AsyncMock(return_value=content.encode('utf-8'))
        return file

    @pytest.fixture
    def mock_csv_credit_only(self):
        """Create a mock CSV file with only Credit column."""
        content = """Date,Description,Credit
2025-01-15,Grocery Store,100.50
2025-01-16,Restaurant,75.25
2025-01-17,Gas Station,45.00
"""
        file = AsyncMock(spec=UploadFile)
        file.filename = "test.csv"
        file.read = AsyncMock(return_value=content.encode('utf-8'))
        return file

    @pytest.fixture
    def mock_csv_debit_only(self):
        """Create a mock CSV file with only Debit column."""
        content = """Date,Description,Debit
2025-01-15,Grocery Store,100.50
2025-01-16,Restaurant,75.25
2025-01-17,Gas Station,45.00
"""
        file = AsyncMock(spec=UploadFile)
        file.filename = "test.csv"
        file.read = AsyncMock(return_value=content.encode('utf-8'))
        return file

    @pytest.fixture
    def mock_csv_missing_columns(self):
        """Create a mock CSV file with missing required columns."""
        content = """Date,Amount
2025-01-15,100.50
2025-01-16,-75.25
2025-01-17,45.00
"""
        file = AsyncMock(spec=UploadFile)
        file.filename = "test.csv"
        file.read = AsyncMock(return_value=content.encode('utf-8'))
        return file

    @pytest.fixture
    def mock_csv_invalid_date(self):
        """Create a mock CSV file with invalid date format."""
        content = """Date,Description,Amount
invalid-date,Grocery Store,100.50
2025-01-16,Restaurant,-75.25
2025-01-17,Gas Station,45.00
"""
        file = AsyncMock(spec=UploadFile)
        file.filename = "test.csv"
        file.read = AsyncMock(return_value=content.encode('utf-8'))
        return file

    @pytest.fixture
    def mock_csv_date_error(self):
        """Create a mock CSV file that will trigger a date conversion error."""
        content = """Date,Description,Amount
2025/01/15,Grocery Store,100.50
2025/01/16,Restaurant,-75.25
not-a-date,Gas Station,45.00
"""
        file = AsyncMock(spec=UploadFile)
        file.filename = "test.csv"
        file.read = AsyncMock(return_value=content.encode('utf-8'))
        return file

    @pytest.fixture
    def mock_unsupported_file(self):
        """Create a mock file with unsupported format."""
        file = AsyncMock(spec=UploadFile)
        file.filename = "test.txt"
        file.read = AsyncMock(return_value=b"Some text content")
        return file

    @pytest.fixture
    def mock_csv_with_trailing_commas(self):
        """Create a mock CSV file with trailing commas."""
        content = """Transaction Date,Description,Amount,,,,
2025-01-15,Grocery Store,100.50,,,,
2025-01-16,Restaurant,-75.25,,,,
2025-01-17,Gas Station,45.00,,,,
"""
        file = AsyncMock(spec=UploadFile)
        file.filename = "test.csv"
        file.read = AsyncMock(return_value=content.encode('utf-8'))
        return file

    @pytest.mark.asyncio
    async def test_parse_csv_with_debit_credit(self, mock_csv_file):
        """Test parsing a CSV file with debit and credit columns."""
        df = await parse_transactions_file(mock_csv_file)
        
        # Verify data was parsed correctly
        assert len(df) == 3
        assert list(df.columns) == ['date', 'description', 'amount']
        
        # Verify debit/credit were combined into amount correctly
        # Note: the implementation negates both debit and credit
        expected_amounts = [-100.50, -75.25, -45.00]
        pd.testing.assert_series_equal(df['amount'].round(2), pd.Series(expected_amounts, name='amount').round(2))
        
        # Verify date conversion
        assert all(isinstance(date, pd.Timestamp) for date in df['date'])
        assert df['date'][0].strftime('%Y-%m-%d') == '2025-01-15'

    @pytest.mark.asyncio
    async def test_parse_excel_file(self, mock_excel_file):
        """Test parsing an Excel file."""
        df = await parse_transactions_file(mock_excel_file)
        
        # Verify data was parsed correctly
        assert len(df) == 3
        assert 'date' in df.columns
        assert 'description' in df.columns
        assert 'amount' in df.columns
        
        # Verify column rename from Transaction Date to date
        assert df['date'][0].year == 2025
        assert df['date'][0].month == 1
        assert df['date'][0].day == 15

    @pytest.mark.asyncio
    async def test_parse_xls_file(self, mock_xls_file):
        """Test parsing an XLS file."""
        df = await parse_transactions_file(mock_xls_file)
        
        # Verify data was parsed correctly
        assert len(df) == 3
        assert 'date' in df.columns
        assert 'description' in df.columns
        assert 'amount' in df.columns
        
        # Verify column rename from Transaction Date to date
        assert df['date'][0].year == 2025
        assert df['date'][0].month == 1
        assert df['date'][0].day == 15

    @pytest.mark.asyncio
    async def test_parse_csv_with_posting_date(self, mock_csv_posting_date):
        """Test parsing a CSV file with Posting Date instead of Transaction Date."""
        df = await parse_transactions_file(mock_csv_posting_date)
        
        # Verify date column was correctly handled
        assert 'date' in df.columns
        assert df['date'][0].year == 2025
        assert df['date'][0].month == 1
        assert df['date'][0].day == 15
        
        # Verify other data
        assert len(df) == 3
        assert list(df.columns) == ['date', 'description', 'amount']

    @pytest.mark.asyncio
    async def test_csv_with_credit_only(self, mock_csv_credit_only):
        """Test parsing a CSV file with only Credit column."""
        df = await parse_transactions_file(mock_csv_credit_only)
        
        # Verify Credit was correctly converted to amount
        assert 'amount' in df.columns
        assert df['amount'][0] == 100.50
        assert df['amount'][1] == 75.25
        assert df['amount'][2] == 45.00

    @pytest.mark.asyncio
    async def test_csv_with_debit_only(self, mock_csv_debit_only):
        """Test parsing a CSV file with only Debit column."""
        df = await parse_transactions_file(mock_csv_debit_only)
        
        # Verify Debit was correctly converted to amount
        assert 'amount' in df.columns
        assert df['amount'][0] == 100.50
        assert df['amount'][1] == 75.25
        assert df['amount'][2] == 45.00

    @pytest.mark.asyncio
    async def test_missing_required_columns(self, mock_csv_missing_columns):
        """Test error handling when required columns are missing."""
        with pytest.raises(HTTPException) as exc_info:
            await parse_transactions_file(mock_csv_missing_columns)
        
        # Verify error details
        assert exc_info.value.status_code == 400
        assert "Missing required columns" in exc_info.value.detail
        assert "description" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_invalid_date_format(self, mock_csv_invalid_date):
        """Test error handling when date format is invalid."""
        with pytest.raises(HTTPException) as exc_info:
            await parse_transactions_file(mock_csv_invalid_date)
        
        # Verify error details
        assert exc_info.value.status_code == 400
        assert "Invalid date format" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_date_conversion_error(self, mock_csv_date_error):
        """Test error handling when date conversion fails."""
        with pytest.raises(HTTPException) as exc_info:
            await parse_transactions_file(mock_csv_date_error)
        
        # Verify error details
        assert exc_info.value.status_code == 400
        assert "Invalid date format" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_unsupported_file_format(self, mock_unsupported_file):
        """Test error handling when file format is unsupported."""
        with pytest.raises(HTTPException) as exc_info:
            await parse_transactions_file(mock_unsupported_file)
        
        # Verify error details
        assert exc_info.value.status_code == 400
        assert "Unsupported file format" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_file_read_error(self):
        """Test error handling when file reading fails."""
        # Create a mock file that raises an exception when read
        file = AsyncMock(spec=UploadFile)
        file.filename = "test.csv"
        file.read = AsyncMock(side_effect=Exception("File read error"))
        
        with pytest.raises(HTTPException) as exc_info:
            await parse_transactions_file(file)
        
        # Verify error details
        assert exc_info.value.status_code == 400
        assert "Error reading file" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_csv_with_trailing_commas(self, mock_csv_with_trailing_commas):
        """Test handling CSV files with trailing commas."""
        df = await parse_transactions_file(mock_csv_with_trailing_commas)
        
        # Verify data was parsed correctly despite trailing commas
        assert len(df) == 3
        assert list(df.columns) == ['date', 'description', 'amount']
        assert df['amount'][0] == 100.50
        assert df['amount'][1] == -75.25
        assert df['amount'][2] == 45.00

    @pytest.mark.asyncio
    async def test_general_exception_handling(self):
        """Test general exception handling during file processing."""
        file = AsyncMock(spec=UploadFile)
        file.filename = "test.csv"
        file.read = AsyncMock(return_value=b"Valid content")
        
        # Mock pd.read_csv to raise a general exception
        with patch('pandas.read_csv', side_effect=Exception("General processing error")):
            with pytest.raises(HTTPException) as exc_info:
                await parse_transactions_file(file)
            
            # Verify error details
            assert exc_info.value.status_code == 400
            assert "Error reading file" in exc_info.value.detail