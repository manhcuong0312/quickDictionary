# Từ điển tra nhanh cho NVDA

* Tác giả: Oleksandr Gryshchenko
* Phiên bản: 2.1
* Tải về [phiên bản chính thức][1]
* Tải về [phiên bản thử nghiệm][2]
* NVDA tương thích: 2019.3 trở lên

Chào mừng đến với add-on  Từ Điển Tra Nhanh của NVDA, cho phép bạn nhanh chóng tạo một bản phiên dịch từ điển  của một từ hay cụm từ ra ngôn ngữ được chọn bằng một phím lệnh. Có vài phím tắt cơ bản. Tất cả chúng đều trực quan và tiện lợi nên bạn sẽ ghi nhớ  chúng một cách nhanh chóng.  
Các bản dịch từ điển chứa các thông tin chi tiết về một từ như một đoạn diễn văn, loại, số nhiều hay số ít, các tùy chọn phiên dịch, danh sách nghĩa, từ đồng nghĩa và ví dụ cụ thể. Các thông tin này sẽ hữu ích cho những ai đang học tiếng nước ngoài hoặc dùng để giao tiếp bằng sự đa dạng phong phú của  tiếng mẹ đẻ.  
Add-on này hỗ trợ vài dịch vụ tra từ điển trực tuyến. Bạn có thể chọn loại từ điển mong muốn trong các hộp thoại thích hợp hoặc dùng phím lệnh. Mỗi dịch vụ sẽ có bản thiết lập riêng của nó.  
Tính năng nâng cao hơn của nó là hoạt động với các hồ sơ giọng đọc. Bạn có thể gán một hồ sơ giọng đọc cho một ngôn ngữ nhất định. Sau đó, nội dung phiên dịch cho ngôn ngữ được chọn sẽ tự đọc bằng giọng đọc đã chọn.  
Dưới đây là tất cả tính năng của add-on và phím tắt để điều khiển chúng. Mặc định, tất cả tính năng dđược gọi bằng hai lớp lệnh. Tuy nhiên, bạn có thể gán lại phím lệnh để tiện cho mình. Bạn có thể làm điều đó thông qua "tùy chọn" trong trình đơn NVDA -> hộp thoại "Quản lý thao tác...".  

## Receiving a dictionary article
In order to get an article from the dictionary, you must first select the word you are interested in or copy it to the clipboard. Then just press NVDA+Y twice.
There is also another way to get a dictionary entry: pressing NVDA+Y once switches the keyboard to add-on control mode, then just use the D key.

## Add-on control mode
To access all the features of the add-on, you need to switch to add-on control mode, you can do this by pressing NVDA+Y once. You will hear a short low beep and will be able to use the other commands described below. When you press a key that is not used in the add-on, you will hear another signal notifying you of an erroneous command and the add-on control mode will be automatically turned off.

## Add-on commands list
Basic dictionary commands:
* D - announce a dictionary entry for a selected word or phrase (same as NVDA+Y);
* W - show dictionary entry in a separate browseable window;
* S - swap languages and get Quick Dictionary translation;
* A - announce the current source and target languages;
* C - copy last dictionary entry to the clipboard;
* E - edit text before sending;
* U - download from online dictionary and save the current list of available languages;
* function keys - select online dictionary service;
* Q - statistics on the using the online service;
* F - choose online service.  

Voice synthesizers profiles management:
* from 1 to 9 - selection of the voice synthesizer profile;
* G - announce the selected profile of voice synthesizers;
* B - back to previous voice synthesizer;
* R - restore default voice synthesizer;
* Del - delete the selected voice synthesizer profile;
* V - save configured voice synthesizer profile;
* P - display a list of all customized voice synthesizers profiles.  

Press O to open add-on settings dialog.

## Help on add-on commands
You can see a list of all the commands used in the add-on as follows:
* Via the NVDA menu - by pressing NVDA+N, go to the submenu "Tools", then - "Quick Dictionary" and activate the menu item "Help on add-on commands".
* Press the H key in add-on control mode (NVDA+Y).

## Add-on help
To open the add-on help - press NVDA+N, go to the "Tools" submenu, then - "Quick Dictionary" and activate the menu item "Help".

## Contributions
We are very grateful to everyone who made the effort to develop, translate and maintain this add-on:
* Cagri Dogan - Turkish translation;
* Wafiqtaher - Arabic translation.

Several good solutions from other developments were used in the Quick Dictionary add-on. Thanks to the authors of the following add-ons:
* Instant Translate - Alexy Sadovoy, Beqa Gozalishvili, Mesar Hameed, Alberto Buffolino and other NVDA contributors.
* To work with voice synthesizers profiles were used ideas from the Switch Synth add-on (thanks to Tyler Spivey).

## Change log

### Version 2.1
* added a dialog to edit the text before sending to remote service;
* separated add-on help page from ReadMe;
* Turkish translation added (thanks to Cagri Dogan).

### Version 2.0
* added the ability to connect other online dictionary services;
* added Lexicala service and its settings panel;
* added a dialog for choosing an online service from the list of available ones;
* added a command to get information about the selected service;
* added a dialog for working with profiles of voice synthesizers;
* implemented the procedure for switching to the previous voice synthesizer;
* implemented a parallel thread to monitor the state of the synthesizer;
* due to an increase in the number of functions in the add-on - help for commands is now displayed in a separate window;
* updated procedure for caching requests to online services;
* added add-on submenu to NVDA menu;
* updated ReadMe.

### Version 1.2
* added the ability to automatically switch voice synthesizers for selected languages;
* added the ability to download the current list of languages available in the online-dictionary;
* Turkish translation added thanks to Cagri Dogan.

### Version 1.1
* changed some keyboard shortcuts which conflicted with other add-ons;
* changed the description of the main add-on features;
* updated help and translation of the add-on;
* removed some keyboard shortcuts and gave to user opportunity to setup them yourself;
* fixed error in Ukrainian translation (thanks to Volodymyr Perig);
* added russian translation.

### Version 1.0: features of implementation
* execution of requests to the remote server in a separate thread to avoid blocking the operation of NVDA;
* signals while waiting for a response from the server;
* caching of the last 100 requests to reduce the load on the remote dictionary service;
* switching to add-on control mode;
* possibility to use an alternative server;
* add-on settings dialog.

## Altering NVDA QuickDictionary
You may clone this repo to make alteration to NVDA Quick Dictionary.

### Third Party dependencies
These can be installed with pip:
- markdown
- scons
- python-gettext

### To package the add-on for distribution:
1. Open a command line, change to the root of this repo
2. Run the **scons** command. The created add-on, if there were no errors, is placed in the current directory.

[1]: https://github.com/grisov/quickDictionary/releases/download/v2.1/quickDictionary-2.1.nvda-addon
[2]: https://github.com/grisov/quickDictionary/releases/download/v2.1/quickDictionary-2.1.nvda-addon
