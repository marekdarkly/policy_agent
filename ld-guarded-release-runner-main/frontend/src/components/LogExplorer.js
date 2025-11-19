import React, { useState, useEffect, useCallback } from 'react';
import { 
  Box, 
  Typography, 
  List, 
  ListItem, 
  ListItemText, 
  Paper, 
  Button, 
  Pagination, 
  CircularProgress,
  Chip,
  Stack,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Divider,
  Alert
} from '@mui/material';
import CloudDownloadIcon from '@mui/icons-material/CloudDownload';
import ArticleIcon from '@mui/icons-material/Article';
import { getLogs } from '../api/simulationApi';

const LogExplorer = ({ simulationStatus, onLogsLoading }) => {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [hasMore, setHasMore] = useState(false);
  const [error, setError] = useState(null);
  const [exportFormat, setExportFormat] = useState('json');
  const [filterText, setFilterText] = useState('');
  
  const logsPerPage = 100;
  
  // Calculate total pages
  const totalPages = Math.ceil(totalCount / logsPerPage) || 1;
  
  // Fetch logs from the server
  const fetchLogs = useCallback(async (currentPage = 1) => {
    setLoading(true);
    if (onLogsLoading) onLogsLoading(true);
    setError(null);
    
    try {
      const skip = (currentPage - 1) * logsPerPage;
      const response = await getLogs(logsPerPage, skip);
      
      setLogs(response.logs);
      setTotalCount(response.total_count);
      setHasMore(response.has_more);
    } catch (err) {
      console.error('Error fetching logs:', err);
      setError('Failed to load logs. Please try again.');
    } finally {
      setLoading(false);
      if (onLogsLoading) onLogsLoading(false);
    }
  }, [onLogsLoading]);
  
  // Load logs when component mounts or page changes
  useEffect(() => {
    fetchLogs(page);
  }, [fetchLogs, page]);
  
  // Generate logs for download
  const generateDownloadData = useCallback(async () => {
    setLoading(true);
    try {
      // Get all logs (up to a reasonable limit, e.g., 10,000)
      const maxLogs = Math.min(10000, totalCount);
      let allLogs = [];
      
      // Fetch logs in batches
      for (let i = 0; i < maxLogs; i += logsPerPage) {
        const response = await getLogs(logsPerPage, i);
        allLogs = [...allLogs, ...response.logs];
        
        if (!response.has_more) break;
      }
      
      if (exportFormat === 'json') {
        // JSON format
        const jsonData = JSON.stringify(allLogs, null, 2);
        const blob = new Blob([jsonData], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        
        const link = document.createElement('a');
        link.href = url;
        link.download = `simulation_logs_${new Date().toISOString().replace(/[:.]/g, '-')}.json`;
        link.click();
        
        URL.revokeObjectURL(url);
      } else {
        // CSV format
        // Check if any logs have user_key to determine if we need that column
        const hasUserKeys = allLogs.some(log => log.user_key !== undefined);
        
        // Create header with user_key column only if needed
        const header = hasUserKeys 
          ? 'Timestamp,Time,Message,UserKey\n' 
          : 'Timestamp,Time,Message\n';
        
        // Create CSV data with user_key field only if it exists
        const csvData = allLogs.map(log => {
          const escapedMessage = log.message.replace(/"/g, '""');
          if (hasUserKeys) {
            const userKey = log.user_key !== undefined ? log.user_key : '';
            return `${log.timestamp},"${log.formatted_time}","${escapedMessage}","${userKey}"`;
          } else {
            return `${log.timestamp},"${log.formatted_time}","${escapedMessage}"`;
          }
        }).join('\n');
        
        const blob = new Blob([header + csvData], { type: 'text/csv' });
        const url = URL.createObjectURL(blob);
        
        const link = document.createElement('a');
        link.href = url;
        link.download = `simulation_logs_${new Date().toISOString().replace(/[:.]/g, '-')}.csv`;
        link.click();
        
        URL.revokeObjectURL(url);
      }
    } catch (err) {
      console.error('Error generating download:', err);
      setError('Failed to generate download. Try again or reduce the number of logs.');
    } finally {
      setLoading(false);
    }
  }, [totalCount, exportFormat]);
  
  // Handle page change
  const handlePageChange = (event, value) => {
    setPage(value);
  };
  
  // Handle export format change
  const handleFormatChange = (event) => {
    setExportFormat(event.target.value);
  };
  
  // Filter logs based on search text
  const filteredLogs = filterText
    ? logs.filter(log => log.message.toLowerCase().includes(filterText.toLowerCase()))
    : logs;
  
  return (
    <Box sx={{ mt: 2 }}>
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}
      
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="body2">
          {loading ? (
            <CircularProgress size={16} sx={{ mr: 1, verticalAlign: 'middle' }} />
          ) : (
            <Chip 
              size="small" 
              color="primary" 
              label={`${totalCount.toLocaleString()} entries`} 
              sx={{ mr: 1 }} 
            />
          )}
          {simulationStatus.total_logs_generated > simulationStatus.max_logs && (
            <Chip 
              size="small" 
              color="warning" 
              label={`Log limit reached (${simulationStatus.max_logs.toLocaleString()})`} 
            />
          )}
        </Typography>
        
        <Stack direction="row" spacing={1}>
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel id="export-format-label">Format</InputLabel>
            <Select
              labelId="export-format-label"
              value={exportFormat}
              label="Format"
              onChange={handleFormatChange}
              size="small"
            >
              <MenuItem value="json">JSON</MenuItem>
              <MenuItem value="csv">CSV</MenuItem>
            </Select>
          </FormControl>
          
          <Button
            variant="outlined"
            size="small"
            startIcon={<CloudDownloadIcon />}
            onClick={generateDownloadData}
            disabled={loading || totalCount === 0}
          >
            Download
          </Button>
        </Stack>
      </Box>
      
      <Paper 
        variant="outlined" 
        sx={{ 
          maxHeight: '500px', 
          overflow: 'auto',
          backgroundColor: 'rgba(0, 0, 0, 0.03)',
          mb: 1
        }}
      >
        {loading && logs.length === 0 ? (
          <Box sx={{ p: 4, textAlign: 'center' }}>
            <CircularProgress size={24} />
            <Typography variant="body2" sx={{ mt: 2 }}>
              Loading logs...
            </Typography>
          </Box>
        ) : filteredLogs.length === 0 ? (
          <Box sx={{ p: 4, textAlign: 'center' }}>
            <ArticleIcon sx={{ fontSize: 40, color: 'text.disabled', mb: 1 }} />
            <Typography variant="body1" color="text.secondary">
              No logs available
            </Typography>
            {filterText && (
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                Try changing your filter criteria
              </Typography>
            )}
          </Box>
        ) : (
          <List dense>
            {filteredLogs.map((log, index) => (
              <ListItem 
                key={`${log.timestamp}-${index}`} 
                divider={index < filteredLogs.length - 1}
                sx={{ 
                  py: 0.75,
                  backgroundColor: log.message.includes('error') || log.message.includes('Error') 
                    ? 'rgba(255, 0, 0, 0.05)' 
                    : undefined
                }}
              >
                <ListItemText
                  primary={
                    <Box sx={{ display: 'flex', gap: 1 }}>
                      <Typography component="span" variant="caption" color="text.secondary" sx={{ minWidth: 75 }}>
                        [{log.formatted_time}]
                      </Typography>
                      <Typography component="span" variant="body2">
                        {log.message}
                      </Typography>
                    </Box>
                  }
                />
              </ListItem>
            ))}
          </List>
        )}
      </Paper>
      
      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
        <Pagination 
          count={totalPages} 
          page={page} 
          onChange={handlePageChange} 
          color="primary" 
          size="small"
          disabled={loading || totalCount === 0}
        />
      </Box>
    </Box>
  );
};

export default LogExplorer; 