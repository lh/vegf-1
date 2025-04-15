# MCP Servers Documentation

This document describes the Model Context Protocol (MCP) servers available in the project and how to use them.

## Overview

MCP servers extend the project's capabilities by providing specialized tools and resources. The servers run locally and are automatically started with VSCode.

## Available Servers

### 1. SQLite Server

The SQLite server provides tools for interacting with SQLite databases in the project.

#### Tools

1. `execute_query`
   - **Purpose**: Execute SQL queries on SQLite databases
   - **Parameters**:
     - `dbPath`: Path to the SQLite database file
     - `query`: SQL query to execute
     - `params` (optional): Query parameters
   - **Example**:
   ```python
   # Execute a query on simulations.db
   {
     "dbPath": "simulations.db",
     "query": "SELECT * FROM simulation_results WHERE id = ?",
     "params": {"id": 123}
   }
   ```

2. `get_schema`
   - **Purpose**: Get schema information for a SQLite database
   - **Parameters**:
     - `dbPath`: Path to the SQLite database file
   - **Example**:
   ```python
   {
     "dbPath": "output/eylea_intervals.db"
   }
   ```

### 2. DocGen Server

The DocGen server helps maintain and validate Python documentation using Numpy-style docstrings.

#### Tools

1. `generate_module_docs`
   - **Purpose**: Generate documentation for a Python module
   - **Parameters**:
     - `module_path`: Path to the Python module
     - `strict_validation` (optional): Enable strict docstring validation
   - **Example**:
   ```python
   {
     "module_path": "simulation/clinical_model.py",
     "strict_validation": true
   }
   ```

2. `validate_docstrings`
   - **Purpose**: Check docstring coverage across the project
   - **Parameters**:
     - `check_coverage` (optional): Enable coverage checking
   - **Example**:
   ```python
   {
     "check_coverage": true
   }
   ```

## Usage Guidelines

1. **Documentation Maintenance**:
   - Use `validate_docstrings` regularly to identify missing documentation
   - Use `generate_module_docs` when working on specific modules to ensure proper docstring formatting

2. **Database Operations**:
   - Use `execute_query` for all SQLite database interactions
   - Check database schemas with `get_schema` before making structural changes

3. **Best Practices**:
   - Always handle errors returned by MCP tools
   - Use appropriate parameters for each tool
   - Consider batching operations when working with multiple files/records

## Configuration

MCP servers are configured in:
```
~/Library/Application Support/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json
```

Each server has its own configuration section including:
- Command to run the server
- Environment variables
- Server-specific settings

## Common Tasks

### Checking Documentation Coverage

```python
# Check entire project for missing docstrings
{
  "check_coverage": true
}
```

### Generating Module Documentation

```python
# Generate docs for a specific module
{
  "module_path": "path/to/module.py",
  "strict_validation": true
}
```

### Database Queries

```python
# Query simulation results
{
  "dbPath": "simulations.db",
  "query": "SELECT * FROM results WHERE simulation_id = :id",
  "params": {"id": "sim123"}
}
```

## Troubleshooting

1. **Server Not Responding**:
   - Check if the server is running in VSCode
   - Restart VSCode if needed
   - Check server logs for errors

2. **Tool Execution Errors**:
   - Verify parameter types and values
   - Check file paths are correct
   - Ensure databases are accessible

3. **Performance Issues**:
   - Process large datasets in batches
   - Use appropriate indexing for databases
   - Consider query optimization

## Future Extensions

The MCP architecture allows for adding new servers as needed. Potential future servers could include:
- Data analysis tools
- Visualization generators
- External API integrations
