# APE Deployment Checklist

## Pre-Deployment Verification

### Code Quality
- [ ] All tests pass: `pytest tests/`
- [ ] No linting errors: `pylint ape/`
- [ ] Imports are clean (no sys.path hacks)
- [ ] No hardcoded paths or secrets

### Functionality Testing
- [ ] APE.py launches without errors
- [ ] Protocol Manager loads and displays protocols
- [ ] Simulations run successfully
- [ ] Analysis pages display results correctly
- [ ] Export/Import functionality works
- [ ] Memory monitoring displays correctly

### Performance
- [ ] Application starts in < 5 seconds
- [ ] Simulations complete in reasonable time
- [ ] No memory leaks during extended use
- [ ] File uploads work within size limits

## Deployment Package

### Required Files
```
✓ APE.py
✓ pages/1_Protocol_Manager.py
✓ pages/2_Simulations.py  
✓ pages/3_Analysis.py
✓ ape/ (all subdirectories)
✓ assets/
✓ protocols/
✓ visualization/
✓ simulation_v2/
✓ .streamlit/config.toml
✓ requirements.txt
✓ README.md
```

### Excluded Files
```
✗ dev/
✗ tests*/
✗ scripts*/
✗ archive/
✗ literature_extraction/
✗ __pycache__/
✗ *.log
✗ .git/
✗ requirements-dev.txt
✗ CLAUDE*.md
```

## Deployment Steps

### 1. Local Testing
```bash
# Clean install
python -m venv test_env
source test_env/bin/activate  # or test_env\Scripts\activate on Windows
pip install -r requirements.txt
streamlit run APE.py
```

### 2. Docker Testing
```bash
# Build image
docker build -t ape-app:test .

# Run container
docker run -p 8501:8501 ape-app:test

# Test at http://localhost:8501
```

### 3. Production Configuration
- [ ] Set appropriate resource limits
- [ ] Configure HTTPS/SSL
- [ ] Set up monitoring/logging
- [ ] Configure backups
- [ ] Set environment variables

### 4. Deploy
- [ ] Tag release: `git tag v1.0.0`
- [ ] Push to deployment branch
- [ ] Deploy container/application
- [ ] Verify health checks pass
- [ ] Test core functionality

## Post-Deployment

### Verification
- [ ] Application accessible at production URL
- [ ] All pages load correctly
- [ ] Can upload and run simulations
- [ ] Performance metrics acceptable
- [ ] Logs showing no errors

### Monitoring Setup
- [ ] CPU/Memory alerts configured
- [ ] Error rate monitoring active
- [ ] Backup verification scheduled
- [ ] Health check endpoint responding

## Rollback Plan

If issues arise:
1. Keep previous version tagged and ready
2. Database/file backups available
3. Quick rollback procedure documented
4. Communication plan for users

## Sign-off

- [ ] Development team approval
- [ ] QA testing complete
- [ ] Security review passed
- [ ] Documentation updated
- [ ] Deployment authorized

Date: _______________
Deployed by: _______________
Version: _______________