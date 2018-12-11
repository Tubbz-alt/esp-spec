# ESP Python Support Library

This python support library helps build applications compatible with the ESP
specification.

## Usage

```py
import esp

def main():
  input = esp.get_input()
  ...
  deps = require_dependencies(
    image1=sentinel2_data(10, 'S', 'DG', 2015, 12, 7, 0)
  )
  image1_dir = deps['image1']
  ...
```

