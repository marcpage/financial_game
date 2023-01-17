#!/usr/bin/env python3

# pylint: disable=line-too-long
""" Handles sending emails

    source from:

    - https://www.geeksforgeeks.org/send-mail-gmail-account-using-python/
    - https://geekflare.com/send-gmail-in-python/
    - https://stackoverflow.com/questions/3902455
    - https://www.tutorialspoint.com/send-mail-with-attachment-from-your-gmail-account-using-python  # noqa: E501
    - https://stackoverflow.com/questions/920910

"""


import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header
from email.mime.base import MIMEBase
from email import encoders


def add_attachments(message, attachments):
    """Attach files to an email message"""
    for filename in [] if attachments is None else attachments:
        contents = attachments[filename].get("contents", None)

        if contents is None:
            with open(
                attachments[filename].get("path", filename), "rb"
            ) as content_file:
                contents = content_file.read()

        mime_type = attachments[filename].get("mime", "application/octet-stream")
        assert (
            mime_type.count("/") == 1
        ), f"bad mime_type: '{mime_type}' for {filename}'"
        payload = MIMEBase(*mime_type.split("/"))
        payload.set_payload(contents)
        encoders.encode_base64(payload)
        payload.add_header("Content-Decomposition", "attachment", filename=filename)
        message.attach(payload)


# pylint: disable=too-many-arguments,unused-argument
def form(
    args,
    recipient,
    subject,
    html_body=None,
    text_body=None,
    attachments=None,
    inlined=None,
    encoding="utf-8",
):
    """Formats an email to be sent
    attachments - {
                    <filename>: {
                        'path': path to file (optional),
                        'contents': binary contents of the file (optional),
                        'mime': mime type (optional defaults to application/octet-stream),
                        }
                    }
    """
    assert html_body is not None or text_body is not None
    message = MIMEMultipart("mixed")

    message["From"] = args.email_from
    message["To"] = recipient
    message["Subject"] = Header(subject, encoding)

    body = (
        message
        if html_body is None or text_body is None
        else MIMEMultipart("alternative")
    )

    if text_body is not None:
        body.attach(MIMEText(text_body, "plain", encoding))

    related = body if inlined is None else MIMEMultipart("related")

    if html_body is not None:
        related.attach(MIMEText(html_body, "html", encoding))
        # TODO: add inlined images   # pylint: disable=fixme

    add_attachments(message, attachments)
    return message.as_string()


# pylint: disable=too-many-arguments
def send(
    args,
    recipient,
    subject,
    html_body=None,
    text_body=None,
    attachments=None,
    inlined=None,
    encoding="utf-8",
):
    """Sends an email"""
    body = form(
        args, recipient, subject, html_body, text_body, attachments, inlined, encoding
    )
    session = smtplib.SMTP(args.smtp_server, args.email_port)

    if args.smtp_tls:
        session.starttls()

    if args.email_password is not None:
        # TODO: Add support for encrypted password in args   # pylint: disable=fixme
        username = args.email_from if args.email_user is None else args.email_user
        session.login(username, args.email_password)

    session.sendmail(args.email_from, recipient, body)
    session.quit()


# pylint: disable=pointless-string-statement
"""


m = MIMEText(s, 'plain', 'utf-8')
m['Subject'] = Header(s, 'utf-8')


# Send an HTML email with an embedded image and a plain text message for
# email clients that don't want to display the HTML.

from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
from email.MIMEImage import MIMEImage

# Define these once; use them twice!
strFrom = 'from@example.com'
strTo = 'to@example.com'

# Create the root message and fill in the from, to, and subject headers
msgRoot = MIMEMultipart('related')
msgRoot['Subject'] = 'test message'
msgRoot['From'] = strFrom
msgRoot['To'] = strTo
msgRoot.preamble = 'This is a multi-part message in MIME format.'

# Encapsulate the plain and HTML versions of the message body in an
# 'alternative' part, so message agents can decide which they want to display.
msgAlternative = MIMEMultipart('alternative')
msgRoot.attach(msgAlternative)

msgText = MIMEText('This is the alternative plain text message.')
msgAlternative.attach(msgText)

# We reference the image in the IMG SRC attribute by the ID we give it below
msgText = MIMEText('<b>Some <i>HTML</i> text</b> and an image.<br><img src="cid:image1"><br>Nifty!', 'html')  # noqa: E501
msgAlternative.attach(msgText)

# This example assumes the image is in the current directory
fp = open('test.jpg', 'rb')
msgImage = MIMEImage(fp.read())
fp.close()

# Define the image's ID as referenced above
msgImage.add_header('Content-ID', '<image1>')
msgRoot.attach(msgImage)

# Send the email (this example assumes SMTP authentication is required)
import smtplib
smtp = smtplib.SMTP()
smtp.connect('smtp.example.com')
smtp.login('exampleuser', 'examplepass')
smtp.sendmail(strFrom, strTo, msgRoot.as_string())
smtp.quit()


attach_file_name = 'TP_python_prev.pdf'
attach_file = open(attach_file_name, 'rb') # Open the file as binary mode
payload = MIMEBase('application', 'octate-stream')
payload.set_payload((attach_file).read())
encoders.encode_base64(payload) #encode the attachment
#add payload header with filename
payload.add_header('Content-Decomposition', 'attachment', filename=attach_file_name)
message.attach(payload)


mixed
    alternative
        text
        related
            html
            inline image
            inline image
    attachment
    attachment


        ssl_context = ssl.create_default_context()
        service = smtplib.SMTP_SSL(self.smtp_server_domain_name, self.port, context=ssl_context)
        service.login(self.sender_mail, self.password)

        for email in emails:
            result = service.sendmail(self.sender_mail, email, f"Subject: {subject}\n{content}")

        service.quit()


    public Multipart build(String messageText, String messageHtml, List<URL> messageHtmlInline, List<URL> attachments) throws MessagingException {  # noqa: E501
        final Multipart mpMixed = new MimeMultipart("mixed");
        {
            // alternative
            final Multipart mpMixedAlternative = newChild(mpMixed, "alternative");
            {
                // Note: MUST RENDER HTML LAST otherwise iPad mail client only renders the last image and no email  # noqa: E501
                addTextVersion(mpMixedAlternative,messageText);
                addHtmlVersion(mpMixedAlternative,messageHtml, messageHtmlInline);
            }
            // attachments
            addAttachments(mpMixed,attachments);
        }

        //msg.setText(message, "utf-8");
        //msg.setContent(message,"text/html; charset=utf-8");
        return mpMixed;
    }

    private Multipart newChild(Multipart parent, String alternative) throws MessagingException {
        MimeMultipart child =  new MimeMultipart(alternative);
        final MimeBodyPart mbp = new MimeBodyPart();
        parent.addBodyPart(mbp);
        mbp.setContent(child);
        return child;
    }

    private void addTextVersion(Multipart mpRelatedAlternative, String messageText) throws MessagingException {  # noqa: E501
        final MimeBodyPart textPart = new MimeBodyPart();
        textPart.setContent(messageText, "text/plain");
        mpRelatedAlternative.addBodyPart(textPart);
    }

    private void addHtmlVersion(Multipart parent, String messageHtml, List<URL> embeded) throws MessagingException {  # noqa: E501
        // HTML version
        final Multipart mpRelated = newChild(parent,"related");

        // Html
        final MimeBodyPart htmlPart = new MimeBodyPart();
        HashMap<String,String> cids = new HashMap<String, String>();
        htmlPart.setContent(replaceUrlWithCids(messageHtml,cids), "text/html");
        mpRelated.addBodyPart(htmlPart);

        // Inline images
        addImagesInline(mpRelated, embeded, cids);
    }

    private void addImagesInline(Multipart parent, List<URL> embeded, HashMap<String,String> cids) throws MessagingException {  # noqa: E501
        if (embeded != null)
        {
            for (URL img : embeded)
            {
                final MimeBodyPart htmlPartImg = new MimeBodyPart();
                DataSource htmlPartImgDs = new URLDataSource(img);
                htmlPartImg.setDataHandler(new DataHandler(htmlPartImgDs));
                String fileName = img.getFile();
                fileName = getFileName(fileName);
                String newFileName = cids.get(fileName);
                boolean imageNotReferencedInHtml = newFileName == null;
                if (imageNotReferencedInHtml) continue;
                // Gmail requires the cid have <> around it
                htmlPartImg.setHeader("Content-ID", "<"+newFileName+">");
                htmlPartImg.setDisposition(BodyPart.INLINE);
                parent.addBodyPart(htmlPartImg);
            }
        }
    }

    private void addAttachments(Multipart parent, List<URL> attachments) throws MessagingException {
        if (attachments != null)
        {
            for (URL attachment : attachments)
            {
                final MimeBodyPart mbpAttachment = new MimeBodyPart();
                DataSource htmlPartImgDs = new URLDataSource(attachment);
                mbpAttachment.setDataHandler(new DataHandler(htmlPartImgDs));
                String fileName = attachment.getFile();
                fileName = getFileName(fileName);
                mbpAttachment.setDisposition(BodyPart.ATTACHMENT);
                mbpAttachment.setFileName(fileName);
                parent.addBodyPart(mbpAttachment);
            }
        }
    }

    public String replaceUrlWithCids(String html, HashMap<String,String> cids)
    {
        html = replaceUrlWithCids(html, COMPILED_PATTERN_SRC_URL_SINGLE, "src='cid:@cid'", cids);
        html = replaceUrlWithCids(html, COMPILED_PATTERN_SRC_URL_DOUBLE, "src=\"cid:@cid\"", cids);
        return html;
    }

    private String replaceUrlWithCids(String html, Pattern pattern, String replacement, HashMap<String,String> cids) {  # noqa: E501
        Matcher matcherCssUrl = pattern.matcher(html);
        StringBuffer sb = new StringBuffer();
        while (matcherCssUrl.find())
        {
            String fileName = matcherCssUrl.group(1);
            // Disregarding file path, so don't clash your filenames!
            fileName = getFileName(fileName);
            // A cid must start with @ and be globally unique
            String cid = "@" + UUID.randomUUID().toString() + "_" + fileName;
            if (cids.containsKey(fileName))
                cid = cids.get(fileName);
            else
                cids.put(fileName,cid);
            matcherCssUrl.appendReplacement(sb,replacement.replace("@cid",cid));
        }
"""
