#!/usr/bin/env python3
"""
Test script to verify that all dependencies are properly installed
"""

import sys
import subprocess

def test_python_version():
    """Test Python version"""
    print("Testing Python version...")
    if sys.version_info >= (3, 7):
        print(f"✅ Python {sys.version.split()[0]} - OK")
        return True
    else:
        print(f"❌ Python {sys.version.split()[0]} - Need 3.7+")
        return False

def test_import(module_name, package_name=None):
    """Test if a module can be imported"""
    try:
        __import__(module_name)
        print(f"✅ {package_name or module_name} - OK")
        return True
    except ImportError:
        print(f"❌ {package_name or module_name} - Not installed")
        return False

def test_ffmpeg():
    """Test if FFmpeg is available"""
    try:
        result = subprocess.run(['ffmpeg', '-version'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ FFmpeg - OK")
            return True
    except FileNotFoundError:
        pass
    
    print("❌ FFmpeg - Not found")
    return False

def test_streamlit_run():
    """Test if Streamlit can run"""
    try:
        result = subprocess.run([sys.executable, '-m', 'streamlit', '--version'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Streamlit CLI - OK")
            return True
    except Exception:
        pass
    
    print("❌ Streamlit CLI - Error")
    return False

def main():
    """Run all tests"""
    print("🧪 Testing YouTube Playlist Downloader Installation")
    print("=" * 50)
    
    tests = [
        ("Python Version", test_python_version),
        ("Streamlit", lambda: test_import("streamlit")),
        ("yt-dlp", lambda: test_import("yt_dlp", "yt-dlp")),
        ("FFmpeg", test_ffmpeg),
        ("Streamlit CLI", test_streamlit_run),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        result = test_func()
        results.append(result)
    
    print("\n" + "=" * 50)
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"🎉 All tests passed! ({passed}/{total})")
        print("\nYou can now run the application with:")
        print("  streamlit run app.py")
    else:
        print(f"⚠️  {passed}/{total} tests passed")
        if not results[0]:  # Python version
            print("\n❌ Python version issue - please upgrade to Python 3.7+")
        if not results[1]:  # Streamlit
            print("\n❌ Streamlit missing - run: pip install streamlit")
        if not results[2]:  # yt-dlp
            print("\n❌ yt-dlp missing - run: pip install yt-dlp")
        if not results[3]:  # FFmpeg
            print("\n❌ FFmpeg missing - install from https://ffmpeg.org/")
        if not results[4]:  # Streamlit CLI
            print("\n❌ Streamlit CLI issue - try reinstalling streamlit")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)