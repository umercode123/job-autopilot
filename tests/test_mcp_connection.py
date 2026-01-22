"""
Test Chrome DevTools MCP Connection
Simple test to verify MCP server works
"""
import subprocess
import json
import time

def test_mcp_connection():
    """
    Test if chrome-devtools MCP server can start
    """
    print("=" * 50)
    print("Testing Chrome DevTools MCP Connection")
    print("=" * 50)
    
    try:
        # Try to run the MCP server
        print("\n📡 Starting MCP server...")
        
        # Windows: use npx.cmd
        npx_cmd = "npx.cmd" if subprocess.os.name == 'nt' else "npx"
        
        print(f"Command: {npx_cmd} -y chrome-devtools-mcp@latest --help")
        
        result = subprocess.run(
            [npx_cmd, "-y", "chrome-devtools-mcp@latest", "--help"],
            capture_output=True,
            text=True,
            timeout=30,
            shell=True  # Use shell on Windows
        )
        
        if result.returncode == 0:
            print("\n✅ MCP server executable found!")
            print("\nOutput:")
            print(result.stdout[:500])  # First 500 chars
            return True
        else:
            print(f"\n❌ Error (exit code: {result.returncode})")
            print(f"Error output: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("\n⏱️ Timeout - MCP server took too long to respond")
        print("This might be normal for first-time npm package download")
        return None
        
    except FileNotFoundError:
        print("\n❌ npx command not found!")
        print("Please install Node.js and npm first")
        return False
        
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        return False


if __name__ == "__main__":
    success = test_mcp_connection()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ MCP Test: PASSED")
        print("=" * 50)
        print("\nNext steps:")
        print("1. MCP server is working")
        print("2. Ready to create Python MCP client")
        print("3. Will use 'mcp' Python package to connect")
    elif success is None:
        print("⏱️ MCP Test: TIMEOUT (might be downloading)")
        print("=" * 50)
        print("Try running again in a few seconds")
    else:
        print("❌ MCP Test: FAILED")
        print("=" * 50)
        print("Please check:")
        print("1. Node.js is installed: node --version")
        print("2. npm is installed: npm --version")
