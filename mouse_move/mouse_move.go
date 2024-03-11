/*
	======================================================================================================
	Little app to move the mouse pointer every so many seconds to avoid the screensaver from kicking in.
	The number of seconds is configurable through a config yaml-file and the app will dynamic detect
	config changes and will apply them on the fly during runtime so that the app does not need to get
	bounced for new settings to take effect.

	------------------------------------------------------------------------------------------------------
	Init the app and download dependencies:
		go mod init mouse_move.go
		go mod tidy

	Build the app:
		go build mouse_move.go

	Run it as a process in the background:
		nohup ./mouse_move 2>&1 > mouse.log &

	Run it as a process in the background through launchd:
		-> see details in the com.jocreyf.mouse_move.plist file

	======================================================================================================
	2020-03-12  v0.1  jcreyf  Initial POC version
	2022-05-31  v1.0  jcreyf  Restructuring things and pushing to git
	2022-06-01  v1.1  jcreyf  Make the mouse move more than 1 pixel and have it done in "smooth" mode
	2022-06-03  v1.2  jcreyf  A simple mouse move seems not enough any longer.  Adding in a mouse click.
	2022-07-05  v1.3  jcreyf  Removing the click again and changing the log output a little.
	2024-03-11	v1.4  jcreyf  Updating to make project compilable through Go v1.22
	======================================================================================================
*/
package main

import (
	"fmt"
	"io/ioutil" // Needed to read the YAML config-file
	"os"
	"os/signal"     // Needed to detect SIGINT and handle it
	"path/filepath" // Needed to get the directory where this app is running from
	"reflect"       // Needed to scan through the appConfig and set default values
	"regexp"        // Needed to check the app's directory
	"strconv"       // Needed to convert appConfig default values from string to integers or boolean
	"strings"
	"syscall"
	"time"

	"github.com/go-vgo/robotgo" // Needed to move the cursor
	"gopkg.in/yaml.v3"          // Needed to parse YAML config
)

var app_version string = "v1.4 (2024-03-11)"
var config *appConfig = nil
var configFileStat os.FileInfo = nil

/*
	Structure of the application's yaml configuration file.
	We are using tags on the struct fields to set default values.
	(see about YAML stuff: https://github.com/go-yaml/yaml/tree/v3.0.1)
*/
type appConfig struct {
	//	Config struct {
	Enabled      bool  `yaml:"enabled" default:"true"`
	Debug        bool  `yaml:"debug" default:"false"`
	DelaySeconds int64 `yaml:"delay_seconds" default:"60"`
	//	}
}

/*
	Function to scan through the configuration structure and see if we got
	values for all fields.  If not, then see if we have a "default value" tag
	on the field and use it.
*/
func setDefaults(ptr interface{}, tag string) error {
	if reflect.TypeOf(ptr).Kind() != reflect.Ptr {
		return fmt.Errorf("Not a pointer")
	}
	v := reflect.ValueOf(ptr).Elem()
	logDebug(fmt.Sprintln(v))
	t := v.Type()
	logDebug(fmt.Sprintln(t))
	logDebug(fmt.Sprintf("fields: %v", t.NumField()))
	for i := 0; i < t.NumField(); i++ {
		logDebug(fmt.Sprintf("field: %v:", t.Field(i).Name))
		logDebug(fmt.Sprintf("  -> value: %v", t.Field(i)))
		logDebug(fmt.Sprintf("  -> type: %v", t.Field(i).Type))
		logDebug(fmt.Sprintf("  -> tags: %v", t.Field(i).Tag))
		logDebug(fmt.Sprintf("  -> default: %v", t.Field(i).Tag.Get(tag)))
		// if defaultVal := t.Field(i).Tag.Get(tag); defaultVal != "-" {
		if defaultVal := t.Field(i).Tag.Get(tag); defaultVal != "" {
			if err := setFieldDefaultValue(v.Field(i), defaultVal); err != nil {
				return err
			}
		} else {
			logDebug(fmt.Sprintf("Field '%v' has no default value", t.Field(i).Name))
		}
	}
	return nil
}

/*
	The setDefaults() function calls this method for each field for which we don't have
	a config value and for which we can set a default value.
*/
func setFieldDefaultValue(field reflect.Value, defaultVal string) error {
	logDebug(fmt.Sprintf("  setField: %v (%v) -> %v", field, field.Kind(), defaultVal))
	if !field.CanSet() {
		return fmt.Errorf("Can't set value\n")
	}
	switch field.Kind() {
	case reflect.Int, reflect.Int64:
		logDebug("   INT")
		if val, err := strconv.ParseInt(defaultVal, 10, 64); err == nil {
			field.Set(reflect.ValueOf(int(val)).Convert(field.Type()))
		}
	case reflect.String:
		logDebug("   STRING")
		field.Set(reflect.ValueOf(defaultVal).Convert(field.Type()))
	case reflect.Bool:
		logDebug("   BOOL")
		//		if val, err := strconv.ParseBool(defaultVal); err == nil {
		//			field.Set(reflect.ValueOf(val).Convert(field.Type()))
		//		}
		val, err := strconv.ParseBool(defaultVal)
		if err != nil {
			log(fmt.Sprintln(err))
		}
		field.Set(reflect.ValueOf(val).Convert(field.Type()))
	}
	return nil
}

/*
	Read and parse the config yaml-file:
	example file:

		config:
			enabled: true
			debug: true
			delay_seconds: 10
*/
func readConfig(filename string) (*appConfig, error) {
	yamlFile, err := ioutil.ReadFile(filename)
	if err != nil {
		return nil, err
	}
	// config := &appConfig{}
	config = &appConfig{}
	// Apply default values on fields in the structure for which we don't have a value for in the yaml:
	setDefaults(config, "default")
	// Now parse the structure:
	err = yaml.Unmarshal(yamlFile, config)
	if err != nil {
		// return nil, fmt.Errorf("in file %q: %v", filename, err)
		log(fmt.Sprintf("in file %q: %v", filename, err))
		os.Exit(1)
	}
	return config, nil
}

/*
	Move the mouse pointer to the upper left corner of the window and click two times to trick
	the system in believing there is user activity.
	The first click will make the system dropdown to appear but the 2nd click closes it again.
*/
func moveMouse() {
	if config.Enabled {
		// https://github.com/go-vgo/robotgo/blob/master/docs/doc.md
		x, y := robotgo.GetMousePos()
		log(fmt.Sprintf("Mouse move x:%v, y:%v", x, y))
		//		robotgo.MoveMouse(0, 0)
		//		robotgo.Click()
		//		robotgo.Click()
		robotgo.MoveMouseSmooth(x+10, y)
		// For some dark reason, the mouse pointer seems to be drifting by 2 pixels consistently if we use
		// the MoveMouseSmooth() method to move back to the original mouse position.  That's not happening
		// when we use the MoveMove() method:
		robotgo.MoveMouse(x, y)
	} else {
		logDebug("Not running (config.enabled == false)")
	}
}

/*
	Log configuration data that we have for this app.
	The data is read from the config-file or default values are being used (hard coded in the appConfig structure above).
*/
func logConfigFileInfo() {
	log(fmt.Sprintf("Config (%v):", configFileStat.ModTime().Format("01-02-2006 15:04:05")))
	log(fmt.Sprintf("  Enabled: %v", config.Enabled))
	log(fmt.Sprintf("  Debug: %v", config.Debug))
	log(fmt.Sprintf("  Delay seconds: %v", config.DelaySeconds))
}
func log(text string) {
	fmt.Printf("%v: %v\n", time.Now().Format("01-02-2006 15:04:05"), text)
}
func logDebug(text string) {
	if config.Debug {
		log("DEBUG: " + text)
	}
}

/*
	Sleep for a number of seconds (configured in config-file).
*/
func wait() {
	logDebug("sleep...")
	time.Sleep(time.Duration(config.DelaySeconds) * time.Second)
}

/*
	Display the app's version information.
*/
func showVersion() {
	// Get the name of the app.
	// This includes the path information, which we need to cut off!
	// Find the last "/" in the path and take all characters after
	// (ignoring any potential arguments that may have been passed on the command line)
	app_name := os.Args[0][strings.LastIndex(os.Args[0], "/")+1:]
	log(fmt.Sprintf("%v - %v", app_name, app_version))
}

func main() {
	var err error = nil
	var configFile string = "mouse_move.yaml"

	// Set a SIGINT (CRTL-C) handler:
	c := make(chan os.Signal)
	signal.Notify(c, os.Interrupt, syscall.SIGTERM)
	go func() {
		<-c
		log("End of app")
		os.Exit(1)
	}()

	// Log the app's version info:
	showVersion()

	// Get the location on disk where this app is running from:
	app, err := os.Executable()
	if err != nil {
		log(fmt.Sprintln(err))
	}
	directory := filepath.Dir(app)
	// The app can be run directly from source or pre-compiled.
	// It's hard to detect the difference since even when run from "source", the app is first compiled into a binary before running it.
	// The best way to detect the difference is probably the fact that the built-from-source binary is stored in some temporary location
	// while the pre-built binary is probably sitting in a non-temp location.
	// The temp-dir is something like:
	//   /var/folders/jq/9t6cmbzd3wl_v3jh5vgmn0y80000gn/T/go-build1688686264/b001/exe/
	// It looks like "/go-build"* and ending with "/exe" are consistant.
	// Lets use some regular expression to detect the one from the other:
	match, _ := regexp.MatchString(".*/go-build.*/exe$", directory)
	if match {
		// Yes, it looks like we're running from a temp "go run <app>" location.
		// Don't expect the config-file here!
		log("RUNNING FROM TEMP LOCATION!")
	} else {
		// It looks like we're probably running a pre-compiled release.
		// Expect the config file in this directory too:
		configFile = fmt.Sprintf("%v/%v", directory, configFile)
	}
	log(fmt.Sprintf("Running from: %v", directory))

	// Read the app's config file:
	log(fmt.Sprintf("Loading config from: %v", configFile))
	config, err = readConfig(configFile)
	if err != nil {
		log(fmt.Sprintln(err))
	}

	// Get some stats of the config-file so that we have something to detect file changes
	// while the app is running:
	configFileStat, err = os.Stat(configFile)
	if err != nil {
		log(fmt.Sprintln(err))
	}
	// Log the configuration settings:
	logConfigFileInfo()

	/*
		Go in an endless loop here, looping through:
			1. move the mouse pointer;
			2. wait the configured number of seconds;
			3. see if yaml-file changed:
				- if yes, then reload it and use the new config values;
				- if "enabled" is now set to false, then stop moving the mouse pointer;
	*/
	for {
		moveMouse()
		wait()
		// Check to see if the config-file changed:
		_configFileStat, err := os.Stat(configFile)
		if err != nil {
			log(fmt.Sprintln(err))
		}
		if _configFileStat.Size() != configFileStat.Size() || _configFileStat.ModTime() != configFileStat.ModTime() {
			log("THE CONFIG-FILE CHANGED DURING RUNTIME!!!")
			log("Reloading and applying the new configuration...")
			// Re-read the app's config file to update the settings at runtime:
			config, err = readConfig(configFile)
			configFileStat = _configFileStat
			logConfigFileInfo()
		}
	}
}
