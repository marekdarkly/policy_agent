import React, { useState, useEffect, useCallback } from "react";
import {
  Box,
  TextField,
  Grid,
  InputAdornment,
  Typography,
  Divider,
  Paper,
  Switch,
  FormControlLabel,
  Chip,
} from "@mui/material";
import { startSimulation } from "../api/simulationApi";
import {
  updateEnvironmentKey,
} from "../api/launchDarklyApi";
import LaunchDarklyResourceCreator from "./LaunchDarklyResourceCreator";

const ConfigForm = ({ disabled, onStatusChange, saveAndStartRef }) => {
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [savedToStorage, setSavedToStorage] = useState({
    sdk_key: false,
    api_key: false,
  });
  const [environment, setEnvironment] = useState("");

  // Update parent component with current status when it changes
  useEffect(() => {
    if (onStatusChange) {
      onStatusChange(error, success);
    }
  }, [error, success, onStatusChange]);

  // Listen for environment key updates
  useEffect(() => {
    const handleEnvironmentUpdate = (event) => {
      console.log(
        "ConfigForm: Environment updated event received:",
        event.detail
      );
      if (event.detail && event.detail.environment_key) {
        setEnvironment(event.detail.environment_key);
      }
    };

    window.addEventListener("environmentKeyUpdated", handleEnvironmentUpdate);

    // Try to get the environment key on mount if we have the necessary info
    const tryInitialEnvironmentFetch = async () => {
      const savedConfig = localStorage.getItem("ldConfig");
      if (savedConfig) {
        try {
          const parsedConfig = JSON.parse(savedConfig);
          if (
            parsedConfig.sdk_key &&
            parsedConfig.api_key &&
            parsedConfig.project_key
          ) {
            if (!parsedConfig.environment_key) {
              console.log(
                "ConfigForm: No environment key found in config, fetching..."
              );
              await updateEnvironmentKey(parsedConfig);
            }
          }
        } catch (err) {
          console.error(
            "ConfigForm: Error checking for initial environment key:",
            err
          );
        }
      }
    };

    tryInitialEnvironmentFetch();

    return () => {
      window.removeEventListener(
        "environmentKeyUpdated",
        handleEnvironmentUpdate
      );
    };
  }, []);

  const [config, setConfig] = useState(() => {
    const savedConfig = localStorage.getItem("ldConfig");

    let initialConfig = {
      sdk_key: "",
      api_key: "",
      project_key: "default",
      flag_key: "test-flag",
      environment_key: "",
      latency_metric_1: "latency",
      error_metric_1: "error-rate",
      business_metric_1: "purchase-completion",
      latency_metric_1_false_range: [50, 100],
      latency_metric_1_true_range: [52, 131],
      error_metric_1_false_converted: 2,
      error_metric_1_true_converted: 4,
      business_metric_1_false_converted: 99,
      business_metric_1_true_converted: 97,
      error_metric_enabled: true,
      latency_metric_enabled: true,
      business_metric_enabled: true,
      evaluations_per_second: 20.0,
    };

    if (savedConfig) {
      try {
        const parsedConfig = JSON.parse(savedConfig);
        initialConfig = { ...initialConfig, ...parsedConfig };

        // If SDK key exists in saved config, mark it as saved
        if (parsedConfig.sdk_key) {
          setSavedToStorage((prev) => ({
            ...prev,
            sdk_key: true,
          }));
        }

        // If API key exists in saved config, mark it as saved
        if (parsedConfig.api_key) {
          setSavedToStorage((prev) => ({
            ...prev,
            api_key: true,
          }));
        }

        // If environment_key exists, set it in state
        if (parsedConfig.environment_key) {
          console.log(
            "Loading environment key from storage:",
            parsedConfig.environment_key
          );
          setEnvironment(parsedConfig.environment_key);
        }
      } catch (e) {
        console.error("Error parsing saved config:", e);
      }
    }

    return initialConfig;
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    
    // If SDK key changed, clear the environment key since it may no longer be valid
    if (name === "sdk_key") {
      console.log("SDK key changed, clearing environment key");
      const updatedConfig = {
        ...config,
        [name]: value,
        environment_key: "", // Clear stale environment key
      };
      setConfig(updatedConfig);
      setEnvironment(""); // Clear the UI display
      setSavedToStorage((prev) => ({
        ...prev,
        sdk_key: false,
      }));
      
      // Update localStorage immediately to clear stale environment_key
      localStorage.setItem("ldConfig", JSON.stringify(updatedConfig));
    } else {
      setConfig({
        ...config,
        [name]: value,
      });
      
      // If API key changed, reset the saved status
      if (name === "api_key") {
        console.log("api_key changed, resetting saved status");
        setSavedToStorage((prev) => ({
          ...prev,
          api_key: false,
        }));
      }
    }

    // Clear error/success when changing values
    setError(null);
    setSuccess(null);
  };

  // Handle toggle changes
  const handleToggleChange = (e) => {
    const { name, checked } = e.target;
    console.log(`Toggle changed: ${name} = ${checked}`);

    // Create updated config
    const updatedConfig = {
      ...config,
      [name]: checked,
    };

    // Update state
    setConfig(updatedConfig);

    // Save to localStorage immediately to ensure changes persist
    // Create a submission copy to ensure proper formatting
    const submissionConfig = { ...updatedConfig };

    // Process ranges for localStorage
    ["latency_metric_1_false_range", "latency_metric_1_true_range"].forEach(
      (rangeKey) => {
        if (typeof submissionConfig[rangeKey] === "string") {
          try {
            const values = submissionConfig[rangeKey]
              .split(",")
              .map((v) => parseInt(v.trim(), 10));
            const validValues = values.filter((v) => !isNaN(v));
            if (validValues.length === 2) {
              submissionConfig[rangeKey] = validValues;
            } else {
              submissionConfig[rangeKey] = rangeKey.includes("false")
                ? [50, 125]
                : [52, 131];
            }
          } catch (err) {
            submissionConfig[rangeKey] = rangeKey.includes("false")
              ? [50, 125]
              : [52, 131];
          }
        }
      }
    );

    // Ensure toggle states are strictly boolean
    [
      "error_metric_enabled",
      "latency_metric_enabled",
      "business_metric_enabled",
    ].forEach((toggleKey) => {
      submissionConfig[toggleKey] = submissionConfig[toggleKey] === true;
    });

    console.log(`Saving toggle state: ${name} = ${submissionConfig[name]}`);
    localStorage.setItem("ldConfig", JSON.stringify(submissionConfig));
  };

  // Add a new function to save configuration without starting simulation
  const handleSaveOnly = async (e) => {
    // If this is triggered by an Enter keypress, prevent default form submission
    if (e && e.key === "Enter") {
      e.preventDefault();
    }

    if (
      !config.sdk_key ||
      !config.api_key ||
      !config.project_key ||
      !config.flag_key
    ) {
      setError("Please fill out all required fields!");
      return;
    }

    try {
      setError(null);
      setSuccess("Saving configuration...");

      const submissionConfig = { ...config };

      // Process range inputs to ensure they are arrays
      ["latency_metric_1_false_range", "latency_metric_1_true_range"].forEach(
        (rangeKey) => {
          if (typeof submissionConfig[rangeKey] === "string") {
            try {
              const values = submissionConfig[rangeKey]
                .split(",")
                .map((v) => parseInt(v.trim(), 10));
              const validValues = values.filter((v) => !isNaN(v));
              if (validValues.length === 2) {
                submissionConfig[rangeKey] = validValues;
              } else {
                submissionConfig[rangeKey] = rangeKey.includes("false")
                  ? [50, 125]
                  : [52, 131];
              }
            } catch (err) {
              submissionConfig[rangeKey] = rangeKey.includes("false")
                ? [50, 125]
                : [52, 131];
            }
          } else if (!Array.isArray(submissionConfig[rangeKey])) {
            submissionConfig[rangeKey] = rangeKey.includes("false")
              ? [50, 125]
              : [52, 131];
          }
        }
      );

      // Make sure all number fields are integers
      [
        "error_metric_1_false_converted",
        "error_metric_1_true_converted",
        "business_metric_1_false_converted",
        "business_metric_1_true_converted",
      ].forEach((field) => {
        if (typeof submissionConfig[field] === "string") {
          submissionConfig[field] = parseInt(submissionConfig[field], 10) || 0;
        }
      });

      // Handle evaluations_per_second as a float
      if (typeof submissionConfig.evaluations_per_second === "string") {
        submissionConfig.evaluations_per_second = parseFloat(submissionConfig.evaluations_per_second) || 20.0;
      }
      // Ensure it's within bounds
      if (submissionConfig.evaluations_per_second < 0.1) {
        submissionConfig.evaluations_per_second = 0.1;
      } else if (submissionConfig.evaluations_per_second > 100) {
        submissionConfig.evaluations_per_second = 100;
      }

      // Ensure toggle states are properly saved as booleans
      [
        "error_metric_enabled",
        "latency_metric_enabled",
        "business_metric_enabled",
      ].forEach((toggleKey) => {
        // Explicitly convert to boolean
        if (
          submissionConfig[toggleKey] === false ||
          submissionConfig[toggleKey] === "false" ||
          submissionConfig[toggleKey] === 0
        ) {
          submissionConfig[toggleKey] = false;
        } else {
          submissionConfig[toggleKey] = true;
        }
      });

      // Try to get the environment key if we don't have it - use the centralized update function
      if (
        submissionConfig.sdk_key &&
        submissionConfig.api_key &&
        submissionConfig.project_key
      ) {
        console.log("Updating environment key during save");
        const environmentKey = await updateEnvironmentKey(submissionConfig);

        // Directly update the environment state if we got a key back
        if (environmentKey) {
          console.log(
            "Setting environment directly after save:",
            environmentKey
          );
          setEnvironment(environmentKey);
        }
      }

      // Save to localStorage
      localStorage.setItem("ldConfig", JSON.stringify(submissionConfig));

      // Mark SDK and API keys as saved
      setSavedToStorage({
        sdk_key: true,
        api_key: true,
      });

      setSuccess("Configuration saved successfully!");
    } catch (error) {
      console.error("Error saving configuration:", error);
      setError(
        error.response?.data?.detail ||
          error.message ||
          "Failed to save configuration"
      );
    }
  };

  // Function to save configuration and start simulation
  // This is exposed to parent component via ref so SimulationControls can call it
  const handleSubmit = useCallback(async (e) => {
    // Only prevent default if this is called from a form submission event
    if (e && e.preventDefault) {
      e.preventDefault();
    }

    try {
      // First save the configuration
      await handleSaveOnly();

      // Then start the simulation with the saved configuration
      const savedConfig = localStorage.getItem("ldConfig");
      if (savedConfig) {
        setSuccess("Starting simulation...");
        await startSimulation(JSON.parse(savedConfig));
        setSuccess("Configuration saved and simulation started!");
      }
    } catch (error) {
      console.error("Error in handleSubmit:", error);
      setError(error.message || "Failed to start simulation");
      throw error; // Re-throw so SimulationControls can handle it
    }
  }, [config]); // eslint-disable-line react-hooks/exhaustive-deps
  
  // Expose saveAndStart function to parent via ref
  useEffect(() => {
    if (saveAndStartRef) {
      saveAndStartRef.current = handleSubmit;
    }
  }, [saveAndStartRef, handleSubmit]);

  // Add a handler for key press on any field
  const handleKeyDown = (e) => {
    if (e.key === "Enter") {
      handleSaveOnly(e);
    }
  };

  // Helper for range inputs display
  const formatRange = (range) => {
    if (Array.isArray(range)) {
      return range.join(", ");
    } else if (typeof range === "string") {
      return range;
    } else if (range === undefined || range === null) {
      return "";
    }
    // Convert anything else to string
    return String(range);
  };

  // Common styles for all sections
  const sectionStyle = { p: 1.2, mb: 1.2 };
  const headerStyle = {
    display: "flex",
    alignItems: "center",
    mb: 0.3,
    minHeight: "28px", // Ensure consistent height even when alerts aren't present
  };

  const titleStyle = {
    fontSize: "1rem",
    fontWeight: "bold",
    color: "warning.main",
    flexShrink: 0,
  };

  const formLabelStyle = {
    margin: 0,
    "& .MuiFormControlLabel-label": {
      fontSize: "0.875rem",
    },
  };

  return (
    <Box
      component="form"
      onSubmit={(e) => {
        e.preventDefault();
        handleSaveOnly(e);
      }}
      noValidate
      sx={{
        "& .MuiTextField-root": { my: 0.5 },
        "& .MuiFormHelperText-root": { margin: 0, fontSize: "0.75rem" },
        "& .MuiInputLabel-root": { fontSize: "0.875rem" },
        "& .MuiInputBase-input": { fontSize: "0.875rem" },
        display: "flex",
        flexDirection: "column",
        height: "100%",
      }}
    >
      <Box sx={{ flex: "1 1 auto", overflow: "auto" }}>
        {/* Section 1: SDK key, API key, Project key, Flag key */}
        <Paper sx={sectionStyle}>
          <Box sx={headerStyle}>
            <Typography variant="body1" sx={titleStyle}>
              LaunchDarkly Connection
            </Typography>
            <Divider sx={{ flex: 1, ml: 1 }} />
          </Box>

          <Grid container spacing={1}>
            <Grid item xs={12} md={6}>
              <TextField
                name="sdk_key"
                label="SDK Key"
                value={config.sdk_key}
                onChange={handleChange}
                onKeyDown={handleKeyDown}
                required
                fullWidth
                disabled={disabled}
                size="small"
                type={savedToStorage.sdk_key ? "password" : "text"}
                margin="dense"
                helperText="Your LaunchDarkly server-side SDK Key"
                InputProps={{
                  endAdornment:
                    environment && savedToStorage.sdk_key ? (
                      <InputAdornment position="end">
                        <Chip
                          label={`Env: ${environment}`}
                          size="small"
                          color="warning"
                          sx={{
                            height: "22px",
                            fontSize: "0.75rem",
                            fontWeight: "bold",
                            color: "white",
                            backgroundColor: "#f59e0b",
                            maxWidth: "180px",
                            "& .MuiChip-label": {
                              padding: "0 8px",
                              whiteSpace: "nowrap",
                              overflow: "hidden",
                              textOverflow: "ellipsis",
                              display: "block",
                            },
                          }}
                        />
                      </InputAdornment>
                    ) : null,
                }}
              />
            </Grid>

            <Grid item xs={12} md={6}>
              <TextField
                name="api_key"
                label="API Key"
                value={config.api_key}
                onChange={handleChange}
                onKeyDown={handleKeyDown}
                required
                fullWidth
                disabled={disabled}
                size="small"
                type={savedToStorage.api_key ? "password" : "text"}
                margin="dense"
                helperText="Your LaunchDarkly API Key with read + write permissions"
              />
            </Grid>

            <Grid item xs={12} md={6}>
              <TextField
                name="project_key"
                label="Project Key"
                value={config.project_key}
                onChange={handleChange}
                onKeyDown={handleKeyDown}
                required
                fullWidth
                disabled={disabled}
                size="small"
                margin="dense"
                helperText="Project where the flag exists"
              />
            </Grid>

            <Grid item xs={12} md={6}>
              <TextField
                name="flag_key"
                label="Flag Key"
                value={config.flag_key}
                onChange={handleChange}
                onKeyDown={handleKeyDown}
                required
                fullWidth
                disabled={disabled}
                size="small"
                margin="dense"
                helperText="Flag key to evaluate and send events to (✨ Auto-creatable ✨)"
              />
            </Grid>
          </Grid>
        </Paper>

        {/* Section: Traffic Configuration */}
        <Paper sx={sectionStyle}>
          <Box sx={headerStyle}>
            <Typography variant="body1" sx={titleStyle}>
              Traffic Configuration
            </Typography>
            <Divider sx={{ flex: 1, ml: 1 }} />
          </Box>

          <Grid container spacing={1}>
            <Grid item xs={12} md={6}>
              <TextField
                name="evaluations_per_second"
                label="Evaluations Per Second"
                value={config.evaluations_per_second}
                onChange={handleChange}
                onKeyDown={handleKeyDown}
                required
                fullWidth
                disabled={disabled}
                size="small"
                margin="dense"
                type="number"
                inputProps={{
                  min: 0.1,
                  max: 100,
                  step: 0.1,
                }}
                helperText="Rate of flag evaluations (min: 0.1, max: 100, default: 20.0)"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <Box
                sx={{
                  display: "flex",
                  alignItems: "center",
                  height: "100%",
                  pl: 2,
                }}
              >
                <Typography variant="body2" color="text.secondary">
                  {config.evaluations_per_second
                    ? `≈ ${(config.evaluations_per_second * 60).toFixed(0)} evaluations/minute`
                    : ""}
                </Typography>
              </Box>
            </Grid>
          </Grid>
        </Paper>

        {/* Section 2: Error metric name, control conversion rate, treatment conversion rate */}
        <Paper sx={sectionStyle}>
          <Box sx={headerStyle}>
            <FormControlLabel
              control={
                <Switch
                  checked={config.error_metric_enabled}
                  onChange={handleToggleChange}
                  name="error_metric_enabled"
                  disabled={disabled}
                  size="small"
                  color="warning"
                />
              }
              label=""
              sx={formLabelStyle}
            />
            <Typography variant="body1" sx={titleStyle}>
              Error Event Configuration
            </Typography>
            <Divider sx={{ flex: 1, ml: 1 }} />
          </Box>

          <Grid container spacing={1}>
            <Grid item xs={12} md={4}>
              <TextField
                name="error_metric_1"
                label="Error Event Key"
                value={config.error_metric_1}
                onChange={handleChange}
                onKeyDown={handleKeyDown}
                required
                fullWidth
                disabled={disabled || !config.error_metric_enabled}
                size="small"
                margin="dense"
                placeholder="error-rate"
                helperText="e.g., error-rate (✨ Auto-creatable ✨)"
              />
            </Grid>

            <Grid item xs={12} md={4}>
              <TextField
                name="error_metric_1_false_converted"
                label="Control Rate"
                value={config.error_metric_1_false_converted}
                onChange={handleChange}
                onKeyDown={handleKeyDown}
                required
                fullWidth
                disabled={disabled || !config.error_metric_enabled}
                size="small"
                margin="dense"
                type="number"
                placeholder="2"
                InputProps={{
                  endAdornment: (
                    <InputAdornment position="end">%</InputAdornment>
                  ),
                }}
                helperText="% chance of error for control"
              />
            </Grid>

            <Grid item xs={12} md={4}>
              <TextField
                name="error_metric_1_true_converted"
                label="Treatment Rate"
                value={config.error_metric_1_true_converted}
                onChange={handleChange}
                onKeyDown={handleKeyDown}
                required
                fullWidth
                disabled={disabled || !config.error_metric_enabled}
                size="small"
                margin="dense"
                type="number"
                placeholder="4"
                InputProps={{
                  endAdornment: (
                    <InputAdornment position="end">%</InputAdornment>
                  ),
                }}
                helperText="% chance of error for treatment"
              />
            </Grid>
          </Grid>
        </Paper>

        {/* Section 3: Latency metric name, control range, treatment range */}
        <Paper sx={sectionStyle}>
          <Box sx={headerStyle}>
            <FormControlLabel
              control={
                <Switch
                  checked={config.latency_metric_enabled}
                  onChange={handleToggleChange}
                  name="latency_metric_enabled"
                  disabled={disabled}
                  size="small"
                  color="warning"
                />
              }
              label=""
              sx={formLabelStyle}
            />
            <Typography variant="body1" sx={titleStyle}>
              Latency Configuration
            </Typography>
            <Divider sx={{ flex: 1, ml: 1 }} />
          </Box>

          <Grid container spacing={1}>
            <Grid item xs={12} md={4}>
              <TextField
                name="latency_metric_1"
                label="Latency Event Key"
                value={config.latency_metric_1}
                onChange={handleChange}
                onKeyDown={handleKeyDown}
                required
                fullWidth
                disabled={disabled || !config.latency_metric_enabled}
                size="small"
                margin="dense"
                placeholder="latency"
                helperText="e.g., latency (✨ Auto-creatable ✨)"
              />
            </Grid>

            <Grid item xs={12} md={4}>
              <TextField
                name="latency_metric_1_false_range"
                label="Control Range"
                value={formatRange(config.latency_metric_1_false_range)}
                onChange={handleChange}
                onKeyDown={handleKeyDown}
                required
                fullWidth
                disabled={disabled || !config.latency_metric_enabled}
                size="small"
                margin="dense"
                placeholder="50, 100"
                helperText="Min, Max for control (comma-separated)"
              />
            </Grid>

            <Grid item xs={12} md={4}>
              <TextField
                name="latency_metric_1_true_range"
                label="Treatment Range"
                value={formatRange(config.latency_metric_1_true_range)}
                onChange={handleChange}
                onKeyDown={handleKeyDown}
                required
                fullWidth
                disabled={disabled || !config.latency_metric_enabled}
                size="small"
                margin="dense"
                placeholder="75, 125"
                helperText="Min, Max for treatment (comma-separated)"
              />
            </Grid>
          </Grid>
        </Paper>

        {/* Section 4: Business metric name, control conversion rate, treatment conversion rate */}
        <Paper sx={sectionStyle}>
          <Box sx={headerStyle}>
            <FormControlLabel
              control={
                <Switch
                  checked={config.business_metric_enabled}
                  onChange={handleToggleChange}
                  name="business_metric_enabled"
                  disabled={disabled}
                  size="small"
                  color="warning"
                />
              }
              label=""
              sx={formLabelStyle}
            />
            <Typography variant="body1" sx={titleStyle}>
              Business Conversion Configuration
            </Typography>
            <Divider sx={{ flex: 1, ml: 1 }} />
          </Box>

          <Grid container spacing={1}>
            <Grid item xs={12} md={4}>
              <TextField
                name="business_metric_1"
                label="Business Event Key"
                value={config.business_metric_1}
                onChange={handleChange}
                onKeyDown={handleKeyDown}
                required
                fullWidth
                disabled={disabled || !config.business_metric_enabled}
                size="small"
                margin="dense"
                placeholder="purchase-completion"
                helperText="e.g., purchase-completion (✨ Auto-creatable ✨)"
              />
            </Grid>

            <Grid item xs={12} md={4}>
              <TextField
                name="business_metric_1_false_converted"
                label="Control Rate"
                value={config.business_metric_1_false_converted}
                onChange={handleChange}
                onKeyDown={handleKeyDown}
                required
                fullWidth
                disabled={disabled || !config.business_metric_enabled}
                size="small"
                margin="dense"
                type="number"
                placeholder="99"
                InputProps={{
                  endAdornment: (
                    <InputAdornment position="end">%</InputAdornment>
                  ),
                }}
                helperText="% chance of conversion for control"
              />
            </Grid>

            <Grid item xs={12} md={4}>
              <TextField
                name="business_metric_1_true_converted"
                label="Treatment Rate"
                value={config.business_metric_1_true_converted}
                onChange={handleChange}
                onKeyDown={handleKeyDown}
                required
                fullWidth
                disabled={disabled || !config.business_metric_enabled}
                size="small"
                margin="dense"
                type="number"
                placeholder="97"
                InputProps={{
                  endAdornment: (
                    <InputAdornment position="end">%</InputAdornment>
                  ),
                }}
                helperText="% chance of conversion for treatment"
              />
            </Grid>
          </Grid>
          
        </Paper>
      </Box>

      {/* Resource creator positioned at the bottom with fixed spacing */}
      <Box
        sx={{ mt: "auto", py: 2, display: "flex", justifyContent: "center" }}
      >
        <LaunchDarklyResourceCreator disabled={disabled} />
      </Box>
    </Box>
  );
};

export default ConfigForm;
