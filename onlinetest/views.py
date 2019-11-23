from django.core.files.storage import FileSystemStorage
from django.shortcuts import render, get_object_or_404, render_to_response
# This may be used instead of Users.DoesNotExist
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext
from django.views import generic
from django.contrib.auth import authenticate, login, logout
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from .forms import clientRegisterForm, StudenLoginForm, saveMarks, TestIdVal, LoginForm, StudentRegForm, StudenLoginForm, savetestdetails, getClientReview, CommentForms

from django.views.decorators.csrf import csrf_protect
# for older versoins of Django use:
# from django.core.urlresolvers import reverse
import ast
import random
import string
from .models import studentProfile, question, testDetails, studentMark, clientsTable
import onlinetest.file_reader
from django.utils.timezone import datetime
import random
# from Crypto.cipher import AES
import time
# for redirecting to home page

def check_if_review_needed(stuMarks):
	result = ""
	for student in stuMarks:
		comments = student.comments
		comments = comments.split("___")
		if len(comments)==0:
			if comments[0]=="":
				result+='0'
			else:
				result+='1'
		else:
			result+='1'
	return result 

def index(request):
	try:
		return render(request, 'onlinetest/index.html')
	except:
		return HttpResponse("Something went wrong")

# for redirecting to student login page


def studentlogin(request):
	try:
		return render(request, 'onlinetest/studentlogin.html')
	except:
		return HttpResponse("Something went wrong")

# for redirecting to client registration page


def clientregister(request):
	try:
		return render(request, 'onlinetest/clientregister.html')
	except:
		return HttpResponse("Something went wrong")

# for redirecting to client login page


def clientlogin(request):
	try:
		return render(request, 'onlinetest/clientlogin.html', {'login_message': ""})
	except:
		return HttpResponse("Something went wrong")


def studentmarksAnalysis(request):
	flag = 0
	try:
		uid = request.session['user_id']
		client1 = clientsTable.objects.get(pk=uid)
		stuMarks = studentMark.objects.filter(client=uid)
		flag = check_if_review_needed(stuMarks)
		return render(request, 'onlinetest/studentmarks.html', {'client_id': client1, 'stuMarks': stuMarks, 'flag': flag})
	except Exception as e:
		print(e)
		return HttpResponse("Something went wrong")

def studentmarksGraphAnalysis(request):
	try:
		uid = request.session['user_id']
		client1 = clientsTable.objects.get(pk=uid)
		tests = testDetails.objects.filter(client_id=uid)
		return render(request, 'onlinetest/studentgraphmarks.html', {'client_id': client1, 'tests':tests})
	except:
		return HttpResponse("Something went wrong")
        

def testMarksGraph(request):
	try:
		test_id = request.GET.get('test_id')
		uid = request.session['user_id']
		stuMarks = studentMark.objects.filter(client=uid).filter(ques_paper_id=test_id)

		num_ques = 0
		try:
			num_ques = len(stuMarks[0].answers)
		except:
			pass

		stuMarksDict = dict()

		for i in stuMarks:
			stuMarksDict[i.email] = i.marks

		return render(request, 
			   		  'onlinetest/studentgraphmarksdisp.html',
			   		  {'client_id': uid,
					   'stuMarksDict': stuMarksDict,
					   'test_id':test_id,
					   'num_ques':num_ques})

	except Exception as e:
		print(e)
		return HttpResponse("Something went wrong")


def addtest(request):
	try:
		uid = request.session['user_id']
		client = clientsTable.objects.get(pk=uid)
		return render(request, 'onlinetest/addtest.html', {'client_id': client})
	except:
		return HttpResponse("Something went wrong")


def studentInfo(request):
	try:
		uid = request.session['user_id']
		client1 = clientsTable.objects.get(pk=uid)
		stuInfo = studentMark.objects.filter(client=uid)
		# print(stuInfo,client1,uid)
		return render(request, 'onlinetest/studentinfo.html', {'client_id': client1, 'stuInfo': stuInfo})
	except:
		return HttpResponse("Something went wrong")

# for redirecting to testID page


def studenthome(request):
	try:
		if request.session.has_key('test_id'):
			return render(request, 'onlinetest/studenthome.html')
		else:
			return HttpResponseRedirect(reverse('onlinetest:studentlogin'))
	except:
		return HttpResponse("Something went wrong")


def home(request):
	try:
		if request.session.has_key('user_id'):
			uid = request.session['user_id']
			try:
				clientobj = clientsTable.objects.get(pk=uid)
				testinfo_list = testDetails.objects.filter(client_id=uid)
				paginator = Paginator(testinfo_list, 3) # Show 5 tests per page

				page = request.GET.get('page')
				try:
					testinfo = paginator.page(page)
				except PageNotAnInteger:
				# If page is not an integer, deliver first page.
					testinfo = paginator.page(1)
				except EmptyPage:
				# If page is out of range (e.g. 9999), deliver last page of results.
					testinfo = paginator.page(paginator.num_pages)
				return render(request, 'onlinetest/clientadmin.html', {'client_id': clientobj, 'test': testinfo})
			except clientsTable.DoesNotExist:
				return HttpResponse("User not found")
		else:
			return render(request, 'onlinetest/index.html')
	except:
		return HttpResponse("Something went wrong")


# for validating client login and redirecting to admin panel


def clientloginVal(request):
	try:
		if request.method == 'POST':
			log = LoginForm(request.POST)
			if log.is_valid():
				try:
					user = clientsTable.objects.get(email=log.cleaned_data.get(
						'email').strip(), pwd=log.cleaned_data.get('pwd').strip())
					request.session['user_id'] = user.id
					useremail = user.email
					return HttpResponseRedirect(reverse('onlinetest:home'))
				except clientsTable.DoesNotExist:
				        return render(request, 'onlinetest/clientlogin.html', {'login_message': "Wrong username or password"})
	except:
		return render(request, 'onlinetest/clientlogin.html', {'login_message': "Wrong username or password"})

# for client registration and redirecting to admin panel


def adminhome(request):
	try:
		if request.method == 'POST':
			signup = clientRegisterForm(request.POST)
			if signup.is_valid():
				try:
					p = clientsTable(
						name=signup.cleaned_data.get('name').strip(),
						email=signup.cleaned_data.get('email').strip(),
						contactNumber=signup.cleaned_data.get(
							'contactNumber').strip(),
						pwd=signup.cleaned_data.get('pwd').strip(),
					)
					p.save()
					request.session['user_id'] = p.id
					# print("*********************************",p.id)
				except clientsTable.DoesNotExist:
					return HttpResponse("Email already registered")
		return HttpResponseRedirect(reverse('onlinetest:home'))
	except:
		return HttpResponse("Email already registed")

# for adding test details


def simple_upload(request):
	try:
		form = savetestdetails(request.POST or None, request.FILES or None)
		if request.method == 'POST' and request.FILES['myfile'] and form.is_valid():
			now = str(datetime.now().strftime("%Y%m%d%H%M"))
			now = now + str(request.session['user_id'])
			myfile = request.FILES['myfile']
			ext = myfile.name[myfile.name.rfind('.'):]
			fs = FileSystemStorage()
			filename = fs.save(now + ext, myfile)
			re_answers = onlinetest.file_reader.file_to_db(
				filename, str(request.session['user_id']), now)
			uploaded_file_url = fs.url(filename)
			# count1 = question.objects.filter(question_id=now)
			p = testDetails(
				test_id=now,
				client_id=str(request.session['user_id']).strip(),
				testtitle=form.cleaned_data.get('testtitle').strip(),
				testduration=form.cleaned_data.get('testduration').strip(),
				re_answers=re_answers,
				# noOfQuestions = abc,
			)
			p.save()
			return render(request, 'onlinetest/addtest.html', {
				'uploaded_file_url': now,
			})
		return render(request, 'onlinetest/addtest.html', {'client_id': client})
	except Exception as e:
		print(e)
		return HttpResponse("Something went wrong")

# for deleting test

def deletetest(request, test_id):
	try:
		test = testDetails.objects.get(pk=test_id)
		questions = question.objects.filter(question_id=test.test_id)
		deleteMarks = studentMark.objects.filter(ques_paper_id=test.test_id)
		test.delete()
		for i in questions:
			questions.delete()

		for j in deleteMarks:
			deleteMarks.delete()
		return HttpResponseRedirect(reverse('onlinetest:home'))
	except:
		return HttpResponse("Cannot Delete Test")


def clientadmin(request):
	try:
		if not request.user.is_authenticated():
			return render(request, 'onlinetest/clientlogin.html', {'login_message':""})
		else:
			tests = Test.objects.filter(user=request.user)
			return render(request, 'onlinetest/clientadmin.html', {'tests': tests})
	except:
		return HttpResponse("Something went wrong")




def studentreview(request):
	try:
		studentid = request.session['studentuid']
		testid = request.session['test_id']
		# user = studentMark.objects.get(pk=studentid)
		ques = question.objects.filter(question_id=testid)
		# print(testid)
		user = studentMark.objects.filter(studentid=studentid).filter(ques_paper_id=testid)[0]
		answers = user.answers
		# re_answers = user.re_answers
		re_answers = testDetails.objects.filter(test_id=testid)[0].re_answers
		noOfQuestions = ques.count()
		marks = user.marks
		print(request.session)
		return render(request, 'onlinetest/review.html', {'studentid':studentid, 'testid':testid, 'user_id':user, 'ques':ques,'answers':answers,'re_answers':re_answers,'marks':marks, 'noOfQuestions': noOfQuestions })
		
		# return render(request, 'onlinetest/review.html', {'studentid':studentid, 'testid':testid, 'user':user, 'ques':ques })
	except Exception as e:
		print(e)
		return HttpResponse("Something went wrong")

def add_review(request):
		print("inside add_review, comments : ",request.GET.get("comment"))
	# try:
		if request.method == 'GET':
				comments = request.GET.get("comment",None);


				test_id = request.session['test_id']
				student_id = request.session['studentuid']
				student = studentMark.objects.filter(ques_paper_id=test_id).filter(studentid=student_id)[0].update(comments=comments)
				# print(student,type(student))
				student.comments= comments
				# student.update(comments=comments)
				student.save()
				# print(test_id,"******")

				student1 = studentMark.objects.filter(ques_paper_id=test_id).filter(studentid=student_id)[0]
				print(student1.comments)

		return HttpResponse("Comments added succesfully")
	# except Exception as e:
		print(e)
		return HttpResponse("Comments failed")

def paper_submit(request):
	try:
		if request.method == 'POST':
			addmarks = saveMarks(request.POST)
			test_id = request.session['test_id']
			student_id = request.session['studentuid']
			obj = testDetails.objects.get(test_id=test_id)
			obj1 = studentProfile.objects.get(pk=student_id)
			# print(test_id,"*****")
			if addmarks.is_valid():
				p = studentMark(
					ques_paper_id=test_id,
					studentid=student_id,
					client=obj.client_id,
					testtitle=obj.testtitle,
					email=obj1.email,
					name=obj1.name,
					marks=addmarks.cleaned_data.get('totalmarks'),
					answers=addmarks.cleaned_data.get('answers'),
				)
				p.save()
				# print(addmarks.cleaned_data.get('answers'))
			else:
			    return HttpResponse("error 1")
		# return HttpResponseRedirect(reverse('onlinetest:studentlogout'))



		return HttpResponseRedirect(reverse('onlinetest:studentreview'))
	except Exception as e:
		print(e)
		return HttpResponse("Something went wrong")

def client_review(request):
	try:
		if request.method == 'POST':
			info = getClientReview(request.POST)
			print(info)
			if info.is_valid():
				ques_paper_id = info.cleaned_data.get('ques_paper_id').strip()
				student_id = info.cleaned_data.get('student_id').strip()
				
				ques = question.objects.filter(question_id = ques_paper_id)

				user = studentMark.objects.filter(studentid = student_id).filter(ques_paper_id=ques_paper_id)[0]
				answers = user.answers

				re_answers = testDetails.objects.filter(test_id=ques_paper_id)[0].re_answers
				noOfQuestions = ques.count()
				marks = user.marks
				return render(request, 'onlinetest/clientreview.html', {'studentid':student_id, 'testid':ques_paper_id, 'user_id':user, 'ques':ques,'answers':answers,'re_answers':re_answers,'marks':marks, 'noOfQuestions': noOfQuestions })

	except Exception as e :
		print(e)
		return HttpResponse("Something went wrong")
# for logout

def clientlogout(request):
	try:
		del request.session['user_id']
		return HttpResponseRedirect(reverse('onlinetest:index'))
	except:
		pass
	return HttpResponseRedirect(reverse('onlinetest:index'))


def studentlogout(request):
	# try:

		test_id = request.session['test_id']
		student_id = request.session['studentuid']

		comment_obj = CommentForms(request.POST)
		# print(comment_obj.get("comments"),type(comment_obj))
		if comment_obj.is_valid():
			print("**********",comment_obj.cleaned_data.get("comments"))
			student = studentMark.objects.filter(ques_paper_id=test_id).filter(studentid=student_id)[0]
			student.comments=comment_obj.cleaned_data.get("comments")
			# print(comment_obj.get("comments"),request.session)
			student.save()

		# del request.session['studentuid']
		# del request.session['test_id']

		return HttpResponseRedirect(reverse('onlinetest:index'))
	# except:
		pass
		return HttpResponseRedirect(reverse('onlinetest:index'))

# for validating test ID and redirecting to student home


def studentReg(request):
	try:
		if request.method == 'POST':
			test_id = request.POST.get('test_id')
			try:
				testfile_id = testDetails.objects.get(test_id=test_id)
				request.session['test_id'] = test_id
			except testDetails.DoesNotExist:
				return HttpResponse("Invalid test ID")
			return render(request, 'onlinetest/studenthome.html', {'login_message':"", 'testid': testfile_id})
	except:
		return HttpResponse("Something went wrong")

# for validating student


def studentLogincheck(request):
	# try:
		if request.method == 'POST':
			log = StudenLoginForm(request.POST)
			if log.is_valid():
				try:
					user = studentProfile.objects.get(email=log.cleaned_data.get('email').strip(),
													  password=log.cleaned_data.get('password').strip())
					request.session['studentuid'] = user.id
					# print("*******************",request.session['test_id'])
					test_id = request.session.get('test_id')
					user.client = user.client #+";"+log.cleaned_data.get('client').strip()
					user.save()
					# print("log ************",log.cleaned_data.get('client').strip())
					try:
						all_studentmark = studentMark.objects.get(studentid= user.id, ques_paper_id=test_id)
						return HttpResponse("<center><h2>Test Already attempted</h2></center>")	
					except:
						return HttpResponseRedirect(reverse('onlinetest:yourtest'))
				except studentProfile.DoesNotExist:
					return HttpResponse("<center><h2>Invalid Username or Password</h2></center>")
	# except:
		return HttpResponse("Something went wrong")

# for student registration


def studentRegSave(request):
	try:
		if request.method == 'POST':
			addstudent = StudentRegForm(request.POST)
			# print(addstudent)
			if addstudent.is_valid():
				emailcheck = studentProfile.objects.filter(
					email=addstudent.cleaned_data.get('email').strip())
				if(emailcheck.count() > 0):
					return HttpResponse("<center><h2>This email is already registered.</h2></center>")
				else:
					p = studentProfile(
						name=addstudent.cleaned_data.get('name').strip(),
						email=addstudent.cleaned_data.get('email').strip(),
						rollno=addstudent.cleaned_data.get('rollno').strip(),
						password=addstudent.cleaned_data.get(
							'password').strip(),
						client=addstudent.cleaned_data.get('client').strip(),
					)
					p.save()
					# print(addstudent.cleaned_data.get('client').strip())
					request.session['studentuid'] = p.id
		return HttpResponseRedirect(reverse('onlinetest:yourtest'))
	except:
		return HttpResponse("Something went wrong")


def yourtest(request):
	try:
		if request.session.has_key('studentuid') and request.session.has_key('test_id'):
			studentid = request.session['studentuid']
			testid = request.session['test_id']
			# print(testid,"***********")
			try:
				user = studentProfile.objects.get(pk=studentid)
				ques = question.objects.filter(question_id=testid)
				noOfQuestions = ques.count()
				time = testDetails.objects.get(test_id=testid)
				return render(request, 'onlinetest/yourtest.html', {'user_id': user, 'ques': ques, 'timer': time, 'noOfQuestions': noOfQuestions})
			except:
				return HttpResponse("This test doesn't exists anymore")
		else:
			return HttpResponseRedirect(reverse('onlinetest:studentlogin'))
	except:
		return HttpResponse("Something went wrong")


def update_scores(request):
	# try:
	# 	if request.method == POST:
	# 		# test_id = request.GET.get("testid")
	# 		k = 1
	k=1